import json
from weakref import WeakSet

from sqlalchemy import inspect, types

from taal import TranslatableString as TaalTranslatableString


pending_translatables = WeakSet()  # to aid debugging


class TranslatableString(types.TypeDecorator):

    impl = types.String

    def process_bind_param(self, value, dialect):
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
