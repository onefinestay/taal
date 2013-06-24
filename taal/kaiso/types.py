import json

from taal import TranslatableString
from kaiso.types import get_type_id


def get_context(manager, obj, attribute_name):
    type_id = get_type_id(type(obj))
    return "taal:kaiso_field:{}:{}".format(type_id, attribute_name)


def get_message_id(manager, obj):
    primary_keys = list(manager.type_registry.get_index_entries(obj))
    return json.dumps(sorted(primary_keys))


def make_from_obj(manager, obj, attribute_name, pending_value=None):
    context = get_context(manager, obj, attribute_name)
    message_id = get_message_id(manager, obj)
    return TranslatableString(
        context=context,
        message_id=message_id,
        pending_value=pending_value
    )
