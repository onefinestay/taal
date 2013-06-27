from weakref import WeakKeyDictionary

from sqlalchemy import event, inspect

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
    """ Wrap any value in ``TranslatableString`` (including None) """
    if isinstance(value, TaalTranslatableString):
        return value

    translatable = make_from_obj(target, initiator.key, value)
    return translatable


def init(target, args, kwargs):
    """ If no value is passed to the constructor for a given translatable
        column, ``set_`` isn't triggered. To make sure we wrap the None,
        explicityly add it to the list of kwargs if missing """
    mapper = inspect(target.__class__)
    for column in mapper.columns:
        if isinstance(column.type, TranslatableString):
            if column.name not in kwargs:
                kwargs[column.name] = None


def load(target, context):
    """ Wrap columns when loading data from the db """
    mapper = inspect(target.__class__)
    for column in mapper.columns:
        if isinstance(column.type, TranslatableString):
            value = getattr(target, column.name)
            translatable = make_from_obj(target, column.name, value)
            setattr(target, column.name, translatable)


def refresh(target, args, attrs):
    mapper = inspect(target.__class__)
    for column_name in attrs:
        if column_name not in mapper.columns:
            continue
        column = mapper.columns[column_name]
        if isinstance(column.type, TranslatableString):
            translatable = make_from_obj(target, column.name)
            setattr(target, column.name, translatable)
    return target


def before_flush(session, flush_context, instances):
    """ Queue up translations to be saved on commit. We don't want to
        save them until commit, but by then we no longer know what's
        changed. At this point we introspect the session to find added,
        changed and deleted objects and save them, along with information
        about the active session and transaction (to handle savepoint
        rollbacks) to the queue (``flush_log``)


        Notes:
            The ``instances`` argument is from a deprecated api
    """

    for target in session.dirty:
        if not session.is_modified(target):
            continue
        mapper = inspect(target.__class__)
        for column in mapper.columns:
            if isinstance(column.type, TranslatableString):
                translator = get_translator(session)
                value = getattr(target, column.name)
                translator.save_translation(value, commit=True)
                pending_translatables.add(value)

    for target in session.new:
        mapper = inspect(target.__class__)
        for column in mapper.columns:
            if isinstance(column.type, TranslatableString):
                value = getattr(target, column.name)
                if value is not None:
                    pending_translatables.add(value)
                    value = value.pending_value
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
    """ Save any pending translations for this session """
    for transaction, target, column, value in flush_log.pop(session, []):
        translator = get_translator(session)
        translatable = make_from_obj(target, column.name, value)
        translator.save_translation(translatable, commit=True)

        old_value = getattr(target, column.name)
        if old_value is not None:
            # we may now have a primary key
            old_value.message_id = translatable.message_id
            # value is now saved. No need to keep around
            old_value.pending_value = None


def after_soft_rollback(session, previous_transaction):
    """ Drop any pending translations from this transaction """
    if session in flush_log:
        flush_log[session] = [
            pending for pending in flush_log[session]
            if pending[0] != previous_transaction]


def register_session(session):
    event.listen(session, 'before_flush', before_flush)
    event.listen(session, 'after_commit', after_commit)
    event.listen(session, 'after_soft_rollback', after_soft_rollback)
