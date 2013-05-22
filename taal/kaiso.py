from __future__ import absolute_import

from taal import (
    TranslationContextManager, translation_manager, TranslatableString)


class TypeTranslationContextManager(TranslationContextManager):
    """ TranslationContextManager for Kaiso types """

    context = "_taal:kaiso_type"

    def __init__(self, storage, **kwargs):
        self.storage = storage

    def list_message_ids(self):
        storage = self.storage
        hierarchy = storage.get_type_hierarchy()
        return (type_[0] for type_ in hierarchy)

    # do i prefer this to monkey-patching?
    # other options?
    # def get_type_hierarchy(self, storage):
        # for type_id, bases, attrs in storage.get_type_hierarchy():
            # label = TranslatableString(
                # context=self.context,
                # message_id=type_id
            # )
            # yield (type_id, label, bases, attrs)


def monkey_patch_kaiso():
    from kaiso.persistence import Storage

    get_type_hierarchy = Storage.get_type_hierarchy

    def get_labeled_type_hierarchy(self):
        for type_id, bases, attrs in get_type_hierarchy(self):
            label = TranslatableString(
                context=TypeTranslationContextManager.context,
                message_id=type_id
            )
            yield (type_id, label, bases, attrs)

    Storage.get_type_hierarchy = get_labeled_type_hierarchy
    monkey_patch_kaiso.get_type_hierarchy = get_type_hierarchy


def unpatch_kaiso():
    from kaiso.persistence import Storage
    try:
        Storage.get_type_hierarchy = monkey_patch_kaiso.get_type_hierarchy
    except AttributeError:
        # not yet patched
        pass


translation_manager.register(TypeTranslationContextManager)
