from __future__ import absolute_import

from kaiso.attributes import String

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


def get_type_hierarchy(storage, start_type_id=None):
    try:
        type_hierarchy = storage.get_type_hierarchy(start_type_id)
    except TypeError:
        # older version of kaiso
        type_hierarchy = storage.get_type_hierarchy()

    for type_id, bases, attrs in type_hierarchy:
        label = TaalTranslatableString(
            context=TypeTranslationContextManager.context,
            message_id=type_id
        )
        yield (type_id, label, bases, attrs)


class TranslatableString(String):
    @staticmethod
    def to_db(value):
        if value is not None:
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Value was {}".format(value))

    @staticmethod
    def to_python(value):
        return TaalTranslatableString()
