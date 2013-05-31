from __future__ import absolute_import

import json

from kaiso.attributes import String
from kaiso.references import get_store_for_object

from taal import (
    TranslationContextManager, translation_manager,
    TranslatableString as TaalTranslatableString)


class TypeTranslationContextManager(TranslationContextManager):
    """ TranslationContextManager for Kaiso types """

    context = "taal:kaiso_type"

    def __init__(self, storage, **kwargs):
        self.storage = storage

    def list_message_ids(self):
        storage = self.storage
        hierarchy = storage.get_type_hierarchy()
        return (type_[0] for type_ in hierarchy)

translation_manager.register(TypeTranslationContextManager)


def get_context(obj, attribute_name):
    manager = get_store_for_object(obj)
    data = manager.serialize(obj)
    type_id = data['__type__']
    return "taal:kaiso_field:{}:{}".format(type_id, attribute_name)


def get_message_id(obj):
    manager = get_store_for_object(obj)
    primary_keys = list(manager.type_registry.get_index_entries(obj))
    return json.dumps(sorted(primary_keys))


class TranslatableString(String):
    @staticmethod
    def to_primitive(value, for_db):
        if not for_db:
            return value

        if value is not None:
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Value was '{}'".format(value))

    @staticmethod
    def to_python(value):
        """ Not needed until we allow data in this field """
        return TaalTranslatableString()
