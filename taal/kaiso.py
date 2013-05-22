from taal import TranslationContextManager, translation_manager


class TypeTranslationContextManager(TranslationContextManager):
    """ TranslationContextManager for Kaiso types """

    context = "_taal:kaiso_type"

    def __init__(self, storage, **kwargs):
        self.storage = storage

    def list_message_ids(self):
        storage = self.storage
        hierarchy = storage.get_type_hierarchy()
        return (type_[0] for type_ in hierarchy)


translation_manager.register(TypeTranslationContextManager)
