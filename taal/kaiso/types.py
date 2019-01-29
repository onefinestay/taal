import json

from kaiso.types import get_type_id
from kaiso.serialize import object_to_db_value

from taal.translatablestring import TranslatableString


def get_context(manager, obj, attribute_name):
    type_id = get_type_id(type(obj))
    return "taal:kaiso_field:{}:{}".format(type_id, attribute_name)


def get_message_id(manager, obj):
    unique_attrs = set()
    for cls, attr_name in manager.type_registry.get_unique_attrs(type(obj)):
        value = getattr(obj, attr_name)
        if value is not None:
            unique_attrs.add((
                get_type_id(cls).lower(),  # backwards compat; was index name
                attr_name,
                object_to_db_value(value),
            ))

    return json.dumps(sorted(unique_attrs))


def make_from_obj(manager, obj, attribute_name, pending_value=None):
    context = get_context(manager, obj, attribute_name)
    message_id = get_message_id(manager, obj)
    return TranslatableString(
        context=context,
        message_id=message_id,
        pending_value=pending_value
    )
