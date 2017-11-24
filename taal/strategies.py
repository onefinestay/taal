from taal.translatablestring import TranslatableString


class Strategy(object):

    def __init__(self, cache, language):
        self.cache = cache
        self.language = language

    def translate(self, translatable):
        try:
            return self.cache[(translatable.context, translatable.message_id)]
        except KeyError:
            return self.translation_missing(translatable)

    def translation_missing(self, translatable):
        raise NotImplementedError

    def recursive_translate(self, translatable):
        if isinstance(translatable, TranslatableString):
            return self.translate(translatable)
        elif isinstance(translatable, dict):
            return dict(
                (key, self.recursive_translate(val))
                for key, val in translatable.iteritems()
            )
        elif isinstance(translatable, list):
            return [self.recursive_translate(item) for item in translatable]
        elif isinstance(translatable, tuple):
            return tuple(self.recursive_translate(item)
                         for item in translatable)
        else:
            return translatable


class NoneStrategy(Strategy):

    def translation_missing(self, translatable):
        return None


class SentinelStrategy(Strategy):

    TRANSLATION_MISSING = "<TranslationMissing sentinel>"

    def translation_missing(self, translatable):
        return self.TRANSLATION_MISSING


class DebugStrategy(Strategy):

    def get_debug_translation(self, translatable):
        return u"[Translation missing ({}, {}, {})]".format(
            self.language, translatable.context, translatable.message_id)

    def translation_missing(self, translatable):
        return self.get_debug_translation(translatable)
