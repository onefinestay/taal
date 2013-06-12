from __future__ import absolute_import

import json
from weakref import WeakKeyDictionary, WeakSet

from sqlalchemy import event, inspect, types
from sqlalchemy.orm.mapper import Mapper

from taal import TranslatableString as TaalTranslatableString, Translator


def get_context(obj, column):
    table = obj.__table__
    return "taal:sa_field:{}:{}".format(table, column)


def get_message_id(obj):
    cls = obj.__class__
    mapper = inspect(cls)
    primary_keys = mapper.primary_key_from_instance(obj)
    if any(key is None for key in primary_keys):
        return None
    return json.dumps(primary_keys)


def make_from_obj(obj, column, value=None):
    context = get_context(obj, column)
    message_id = get_message_id(obj)
    return TaalTranslatableString(
        context=context,
        message_id=message_id,
        value=value
    )


class TranslatableString(types.TypeDecorator):

    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        if value in _pending_translatables:
            _pending_translatables.remove(value)
        else:
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Use ``set_translation`` instead "
                "Value was '{}'".format(value))


def _set(target, value, oldvalue, initiator):
    if value is None:
        return value

    if isinstance(value, TaalTranslatableString):
        return value

    translatable = make_from_obj(target, initiator.key, value)
    return translatable


def _load(target, context):
    mapper = inspect(target.__class__)
    for column in mapper.columns:
        if isinstance(column.type, TranslatableString):
            value = getattr(target, column.name)
            translatable = make_from_obj(target, column.name, value)
            setattr(target, column.name, translatable)


def _refresh(target, args, kwargs):
    mapper = inspect(target.__class__)
    for column_name in kwargs:
        column = mapper.columns[column_name]
        if isinstance(column.type, TranslatableString):
            value = getattr(target, column.name)
            if isinstance(value, TaalTranslatableString):
                # TODO: is this reachable?
                import ipdb
                ipdb.set_trace()
                continue
            translatable = make_from_obj(target, column.name, value)
            setattr(target, column.name, translatable)
    return target


def _before_flush(session, flush_context, instances):
    for target in session.dirty:
        mapper = inspect(target.__class__)
        for column in mapper.columns:
            if isinstance(column.type, TranslatableString):
                translator = get_translator(session)
                value = getattr(target, column.name)
                translator.set_translation(value, commit=True)
                _pending_translatables.add(value)

    for target in session.new:
        mapper = inspect(target.__class__)
        for column in mapper.columns:
            if isinstance(column.type, TranslatableString):
                value = getattr(target, column.name)
                _flush_log.setdefault(session, []).append(
                    (session.transaction, target, column, value.value))
                _pending_translatables.add(value)

    for target in session.deleted:
        mapper = inspect(target.__class__)
        for column in mapper.columns:
            if isinstance(column.type, TranslatableString):
                translator = get_translator(session)
                translator.delete_translation(
                    getattr(target, column.name), commit=True)


def _after_commit(session):
    for transaction, target, column, value in _flush_log.pop(session, []):
        translator = get_translator(session)
        translatable = make_from_obj(target, column.name, value)
        translator.set_translation(translatable, commit=True)


def _after_soft_rollback(session, previous_transaction):
    if session in _flush_log:
        _flush_log[session] = [
            pending for pending in _flush_log[session]
            if pending[0] != previous_transaction]


def _register_listeners(mapper, cls):
    for column in mapper.columns:
        if isinstance(column.type, TranslatableString):
            event.listen(cls, 'load', _load)
            event.listen(cls, 'refresh', _refresh)

            column_attr = getattr(cls, column.name)
            event.listen(column_attr, 'set', _set, retval=True)

event.listen(Mapper, 'mapper_configured', _register_listeners)


_translator_registry = WeakKeyDictionary()
_flush_log = WeakKeyDictionary()

# to aid debugging
_pending_translatables = WeakSet()


def register_translator(owner, translator):
    _translator_registry[owner] = translator


def get_translator(owner):
    return _translator_registry[owner]


def register_for_translation(session, translator_session, model, language):
    translator = Translator(model, translator_session, language)
    register_translator(session, translator)
    event.listen(session, 'before_flush', _before_flush)
    event.listen(session, 'after_commit', _after_commit)
    event.listen(session, 'after_soft_rollback', _after_soft_rollback)
