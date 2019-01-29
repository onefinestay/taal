from weakref import WeakKeyDictionary

from sqlalchemy import event, inspect
from sqlalchemy.orm.attributes import get_history

from taal.sqlalchemy.types import (
    TranslatableString, pending_translatables, make_from_obj,
    translatable_models)
from taal.constants import PlaceholderValue
from taal.translatablestring import (
    is_translatable_value,
    TranslatableString as TaalTranslatableString,
)


translator_registry = WeakKeyDictionary()
flush_log = WeakKeyDictionary()


def register_translator(owner, translator):
    translator_registry[owner] = translator


def get_translator(owner):
    return translator_registry[owner]


def get_attr_name(obj, column):
    cls = obj.__class__
    attr_name = translatable_models[cls][column]
    return attr_name


def set_(target, value, oldvalue, initiator):
    """ Wrap any value in ``TranslatableString``, except None and the empty
    string
    """
    if not is_translatable_value(value):
        return value

    if isinstance(value, TaalTranslatableString):
        return TaalTranslatableString(
            value.context, value.message_id, value.pending_value)

    translatable = make_from_obj(target, initiator.key, value)
    return translatable


def load(target, context):
    """ Wrap columns when loading data from the db """
    mapper = inspect(target.__class__)
    for column in mapper.columns:
        if isinstance(column.type, TranslatableString):
            value = getattr(target, column.name)
            if not is_translatable_value(value):
                continue
            elif value is PlaceholderValue:
                translatable = make_from_obj(target, column.name, value)
                setattr(target, column.name, translatable)
            elif isinstance(value, TaalTranslatableString):
                continue  # during session.merge
            else:
                raise TypeError("Unexpected column value '{}'".format(
                    value))


def refresh(target, args, attrs):
    mapper = inspect(target.__class__)
    if attrs is None:
        attrs = mapper.columns.keys()

    for column_name in attrs:
        if column_name not in mapper.columns:
            continue
        column = mapper.columns[column_name]
        if isinstance(column.type, TranslatableString):
            value = getattr(target, column.name)
            if is_translatable_value(value):
                translatable = make_from_obj(target, column.name, value)
                setattr(target, column.name, translatable)
    return target


def add_to_flush_log(session, target, delete=False):
    cls = target.__class__
    for column, attr_name in translatable_models.get(cls, {}).items():
        history = get_history(target, attr_name)
        if not delete and not history.has_changes():
            # for non-delete actions, we're only interested in changed columns
            continue

        if delete:
            value = None  # will trigger deletion of translations
        else:
            value = getattr(target, attr_name)
        if is_translatable_value(value):
            pending_translatables.add(value)
            value = value.pending_value
        flush_log.setdefault(session, []).append(
            (session.transaction, target, column, value))


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
        if session.is_modified(target):
            add_to_flush_log(session, target)

    for target in session.new:
        add_to_flush_log(session, target)

    for target in session.deleted:
        add_to_flush_log(session, target, delete=True)


def after_bulk_update(update_context):
    # bulk updating to None would be ok, but leaves dangling Translations
    result = update_context.result
    for bind in result.context.compiled.binds.values():
        field_type = bind.type
        if isinstance(field_type, TranslatableString):
            raise NotImplementedError("Bulk updates are not yet supported")


def after_commit(session):
    """ Save any pending translations for this session """
    for transaction, target, column, value in flush_log.pop(session, []):
        translator = get_translator(session)

        translatable = make_from_obj(target, column.name, value)
        if is_translatable_value(value):
            translator.save_translation(translatable, commit=True)
        else:
            # a non-translatable value in the commit log indicates a deletion
            translator.delete_translations(translatable)

        attr_name = get_attr_name(target, column)
        old_value = getattr(target, attr_name)
        if is_translatable_value(old_value):
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
    event.listen(session, 'after_bulk_update', after_bulk_update)
    event.listen(session, 'after_commit', after_commit)
    event.listen(session, 'after_soft_rollback', after_soft_rollback)
