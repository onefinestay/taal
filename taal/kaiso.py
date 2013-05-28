from __future__ import absolute_import

from taal import (
    TranslationContextManager, translation_manager, TranslatableString)


class TypeTranslationContextManager(TranslationContextManager):
    """ TranslationContextManager for Kaiso types """

    context = "taal:kaiso_type"

    def __init__(self, storage, **kwargs):
        self.storage = storage

    def list_message_ids(self):
        storage = self.storage
        hierarchy = storage.get_type_hierarchy()
        return (type_[0] for type_ in hierarchy)


def get_type_hierarchy(storage):
    for type_id, bases, attrs in storage.get_type_hierarchy():
        label = TranslatableString(
            context=TypeTranslationContextManager.context,
            message_id=type_id
        )
        yield (type_id, label, bases, attrs)


translation_manager.register(TypeTranslationContextManager)
