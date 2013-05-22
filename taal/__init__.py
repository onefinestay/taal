class TranslatableString(object):
    def __init__(self, message_id, context=None):
        self.message_id = message_id
        self.context = context


class Translator(object):
    def __init__(self, model, session):
        self.model = model
        self.session = session

    def translate(self, translatable, language):
        context = translatable.context
        message_id = translatable.message_id

        context_col = getattr(self.model, 'context')
        message_id_col = getattr(self.model, 'message_id')
        language_col = getattr(self.model, 'language')
        translation = self.session.query(
            context_col == context,
            message_id_col == message_id,
            language_col == language
        ).one()

        return translation
