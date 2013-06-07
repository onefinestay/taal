from __future__ import absolute_import

import json

from kaiso.attributes import String
from kaiso.types import get_type_id

from taal import TranslationContextManager, translation_manager


class TypeTranslationContextManager(TranslationContextManager):
    """ TranslationContextManager for Kaiso types """

    context = "taal:kaiso_type"

    def __init__(self, manager, **kwargs):
        self.manager = manager

    def list_message_ids(self):
        manager = self.manager
        type_hierarchy = manager.get_type_hierarchy()
        return (type_[0] for type_ in type_hierarchy)

translation_manager.register(TypeTranslationContextManager)


class AttributeTranslationContextManager(TranslationContextManager):
    """ TranslationContextManager for Kaiso attributes """

    context = "taal:kaiso_attr"

    def __init__(self, manager, **kwargs):
        self.manager = manager

    @staticmethod
    def get_message_id(type_id, attr):
        return json.dumps(
            [type_id, attr.name]
        )

    def list_message_ids(self):
        manager = self.manager
        type_hierarchy = manager.get_type_hierarchy()
        for type_id, bases, attrs in type_hierarchy:
            for attr in attrs:
                yield self.get_message_id(
                    type_id, attr)

translation_manager.register(AttributeTranslationContextManager)


def get_context(manager, obj, attribute_name):
    type_id = get_type_id(type(obj))
    return "taal:kaiso_field:{}:{}".format(type_id, attribute_name)


def get_message_id(manager, obj):
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
