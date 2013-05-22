from taal import TranslationContext, translation_manager


class TypeTranslationContext(TranslationContext):
    """ TranslationContext for Kaiso types """

    identifier = "_taal:kaiso_type"

    def __init__(self, **kwargs):
        self.storage = kwargs['storage']

    def list_message_ids(self):
        storage = self.storage
        hierarchy = storage.get_type_hierarchy()
        return (type_[0] for type_ in hierarchy)


translation_manager.register(TypeTranslationContext)
