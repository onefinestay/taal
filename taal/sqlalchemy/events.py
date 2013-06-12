from weakref import WeakKeyDictionary

from sqlalchemy import event, inspect
from sqlalchemy.orm.mapper import Mapper

from taal import TranslatableString as TaalTranslatableString
from taal.sqlalchemy.types import (
    TranslatableString, pending_translatables, make_from_obj)


translator_registry = WeakKeyDictionary()
flush_log = WeakKeyDictionary()


def register_translator(owner, translator):
    translator_registry[owner] = translator


def get_translator(owner):
    return translator_registry[owner]


def set_(target, value, oldvalue, initiator):
    if value is None:
        return value

    if isinstance(value, TaalTranslatableString):
        return value

    translatable = make_from_obj(target, initiator.key, value)
    return translatable


def load(target, context):
    mapper = inspect(target.__class__)
    for column in mapper.columns:
        if isinstance(column.type, TranslatableString):
            value = getattr(target, column.name)
            translatable = make_from_obj(target, column.name, value)
            setattr(target, column.name, translatable)


def refresh(target, args, attrs):
    mapper = inspect(target.__class__)
    for column_name in attrs:
        column = mapper.columns[column_name]
        if isinstance(column.type, TranslatableString):
            translatable = make_from_obj(target, column.name)
            setattr(target, column.name, translatable)
    return target


def before_flush(session, flush_context, instances):
    for target in session.dirty:
        mapper = inspect(target.__class__)
        for column in mapper.columns:
            if isinstance(column.type, TranslatableString):
                translator = get_translator(session)
                value = getattr(target, column.name)
                translator.set_translation(value, commit=True)
                pending_translatables.add(value)

    for target in session.new:
        mapper = inspect(target.__class__)
        for column in mapper.columns:
            if isinstance(column.type, TranslatableString):
                value = getattr(target, column.name)
                if value is not None:
                    pending_translatables.add(value)
                    value = value.value
                flush_log.setdefault(session, []).append(
                    (session.transaction, target, column, value))

    for target in session.deleted:
        mapper = inspect(target.__class__)
        for column in mapper.columns:
            if isinstance(column.type, TranslatableString):
                translator = get_translator(session)
                translator.delete_translation(
                    getattr(target, column.name), commit=True)


def after_commit(session):
    for transaction, target, column, value in flush_log.pop(session, []):
        translator = get_translator(session)
        translatable = make_from_obj(target, column.name, value)
        translator.set_translation(translatable, commit=True)


def after_soft_rollback(session, previous_transaction):
    if session in flush_log:
        flush_log[session] = [
            pending for pending in flush_log[session]
            if pending[0] != previous_transaction]


def register_listeners(mapper, cls):
    for column in mapper.columns:
        if isinstance(column.type, TranslatableString):
            event.listen(cls, 'load', load)
            event.listen(cls, 'refresh', refresh)

            column_attr = getattr(cls, column.name)
            event.listen(column_attr, 'set', set_, retval=True)


def register_session(session):
    event.listen(session, 'before_flush', before_flush)
    event.listen(session, 'after_commit', after_commit)
    event.listen(session, 'after_soft_rollback', after_soft_rollback)


event.listen(Mapper, 'mapper_configured', register_listeners)
