from taal import TranslationContext


class TypeTranslationContext(TranslationContext):
    """ TranslationContext for Kaiso types """

    def __init__(self, storage):
        self.storage = storage

    def list_message_ids(self):
        storage = self.storage
        hierarchy = storage.get_type_hierarchy()
        return (type_[0] for type_ in hierarchy)
