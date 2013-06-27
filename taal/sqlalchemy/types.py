import json
from weakref import WeakSet

from sqlalchemy import event, inspect, types
from sqlalchemy.orm.mapper import Mapper

from taal import TranslatableString as TaalTranslatableString


CONTEXT_TEMPLATE = "taal:sa_field:{}:{}"


pending_translatables = WeakSet()  # to aid debugging


class TranslatableString(types.TypeDecorator):

    impl = types.Text

    def process_bind_param(self, value, dialect):
        if not isinstance(value, TaalTranslatableString):
            # this should only happen if someone is trying to query
            # TODO: verify this
            raise RuntimeError("Cannot filter on translated fields")

        if value.is_unset():
            return None

        if value in pending_translatables:
            pending_translatables.remove(value)
        else:
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Use ``save_translation`` instead "
                "Value was '{}'".format(value))


def get_context(obj, column):
    table = obj.__table__
    return CONTEXT_TEMPLATE.format(table, column)


def get_message_id(obj):
    cls = obj.__class__
    mapper = inspect(cls)
    primary_keys = mapper.primary_key_from_instance(obj)
    if any(key is None for key in primary_keys):
        return None
    return json.dumps(primary_keys)


def make_from_obj(obj, column, pending_value=None):
    context = get_context(obj, column)
    message_id = get_message_id(obj)

    if pending_value is None:
        pending_value = getattr(obj, column)

    if isinstance(pending_value, TaalTranslatableString):
        pending_value = pending_value.pending_value

    return TaalTranslatableString(
        context=context,
        message_id=message_id,
        pending_value=pending_value
    )


@event.listens_for(Mapper, 'mapper_configured')
def register_listeners(mapper, cls):
    for column in mapper.columns:
        if isinstance(column.type, TranslatableString):
            from taal.sqlalchemy import events
            event.listen(cls, 'init', events.init)
            event.listen(cls, 'load', events.load)
            event.listen(cls, 'refresh', events.refresh)

            column_attr = getattr(cls, column.name)
            event.listen(column_attr, 'set', events.set_, retval=True)
