import json
from weakref import WeakSet

from sqlalchemy import event, inspect, types
from sqlalchemy.orm.mapper import Mapper

from taal import TranslatableString as TaalTranslatableString


CONTEXT_TEMPLATE = "taal:sa_field:{}:{}"
NOT_NULL = "taal:placeholder"


pending_translatables = WeakSet()  # to aid debugging


class NotNullValue(object):
    pass


class TranslatableString(types.TypeDecorator):

    impl = types.Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif value == "":
            return ""

        if not isinstance(value, TaalTranslatableString):
            # this should only happen if someone is trying to query
            # TODO: verify this
            raise RuntimeError("Cannot filter on translated fields")

        if value in pending_translatables:
            pending_translatables.remove(value)
        else:
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Use ``save_translation`` instead "
                "Value was '{}'".format(value))

        return NOT_NULL

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        elif value == "":
            return ""
        elif value == NOT_NULL:
            # can't prevent this from being returned to the user
            # in the case of a direct query for Model.field
            # Return something that's more likely to error early
            # than a string
            return NotNullValue

        raise RuntimeError(
            "Unexpected value found in placeholer column: '{}'".format(
                value))


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


def make_from_obj(obj, column, pending_value):
    context = get_context(obj, column)
    message_id = get_message_id(obj)

    if pending_value is NotNullValue:
        pending_value = None

    if isinstance(pending_value, TaalTranslatableString):
        raise TypeError("pending_value must be a string. Was '{}'".format(
            pending_value))

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
            event.listen(cls, 'load', events.load)
            event.listen(cls, 'refresh', events.refresh)

            column_attr = getattr(cls, column.name)
            event.listen(column_attr, 'set', events.set_, retval=True)
