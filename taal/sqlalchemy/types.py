import json
from weakref import WeakSet

from sqlalchemy import event, inspect, types
from sqlalchemy.orm.mapper import Mapper

from taal.constants import PLACEHOLDER, PlaceholderValue
from taal.translatablestring import (
    is_translatable_value,
    TranslatableString as TaalTranslatableString,
)


CONTEXT_TEMPLATE = "taal:sa_field:{}:{}"
pending_translatables = WeakSet()  # to aid debugging
translatable_models = {}  # cache calls to sqlalchemy inspect


class TranslatableString(types.TypeDecorator):

    impl = types.Text

    def process_bind_param(self, value, dialect):
        if not is_translatable_value(value):
            return value

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

        return PLACEHOLDER

    def process_result_value(self, value, dialect):

        if not is_translatable_value(value):
            return value

        if value == PLACEHOLDER:

            # can't prevent this from being returned to the user
            # in the case of a direct query for Model.field
            # Return something that's more likely to error early
            # than a string
            return PlaceholderValue

        raise RuntimeError(
            "Unexpected value found in placeholder column: '{}'".format(value))


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

    if pending_value is PlaceholderValue:
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
    from taal.sqlalchemy import events

    for column_attr in mapper.column_attrs:
        for column in column_attr.columns:
            if not isinstance(column.type, TranslatableString):
                continue

            if cls not in translatable_models:
                translatable_models[cls] = {}
                event.listen(cls, 'load', events.load)
                event.listen(cls, 'refresh', events.refresh)

            translatable_models[cls][column] = column_attr.key

            event.listen(column_attr, 'set', events.set_, retval=True)
