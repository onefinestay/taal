from __future__ import absolute_import

from abc import ABCMeta, abstractmethod, abstractproperty

from sqlalchemy.orm.exc import NoResultFound


try:
    VERSION = __import__('pkg_resources').get_distribution('taal').version
except:  # pragma: no cover
    VERSION = 'unknown'


class TranslatableString(object):
    def __init__(self, context=None, message_id=None, value=None):
        self.context = context
        self.message_id = message_id
        self.value = value

    def __repr__(self):
        return "<TranslatableString: ({}, {}, {})>".format(
            self.context, self.message_id, self.value)

    def __eq__(self, other):
        self_dict = getattr(self, '__dict__', None)
        other_dict = getattr(other, '__dict__', None)
        return self_dict == other_dict


class Translator(object):
    def __init__(self, model, session, language, debug_output=False):
        self.model = model
        self.session = session
        self.language = language
        self.debug_output = debug_output

    def _translate(self, translatable):
        context = translatable.context
        message_id = translatable.message_id

        try:
            translation = self.session.query(self.model).filter_by(
                context=context,
                message_id=message_id,
                language=self.language
            ).one()
            return translation.value
        except NoResultFound:
            if self.debug_output:
                return "[Translation missing ({}, {}, {})]".format(
                    self.language, context, message_id)
            else:
                return None

    def translate(self, translatable):
        if isinstance(translatable, TranslatableString):
            return self._translate(translatable)
        elif isinstance(translatable, dict):
            return dict(
                (key, self.translate(val))
                for key, val in translatable.iteritems()
            )
        elif isinstance(translatable, list):
            return list(
                self.translate(item)
                for item in translatable)

        else:
            return translatable

    def set_translation(self, translatable, commit=True):
        if translatable.message_id is None:
            raise RuntimeError(
                "Cannot save translatable '{}'. "
                "Message id is None".format(translatable))

        translation = self.model(
            context=translatable.context,
            message_id=translatable.message_id,
            language=self.language
        )

        # we can use merge for 'on duplicate key update'
        # (only works in sqla if we're matching on the primary key)
        translation = self.session.merge(translation)
        translation.value = translatable.value

        if commit:
            self.session.commit()

    def delete_translation(self, translatable, commit=True):
        self.session.query(self.model).filter_by(
            context=translatable.context,
            message_id=translatable.message_id,
            language=self.language
        ).delete()

        if commit:
            self.session.commit()


class TranslationContextManager(object):
    """ Knows all available ``message_id``s for a given context """

    __metaclass__ = ABCMeta

    @abstractproperty
    def context(self):
        """ String used to identify translations managed by this manager """

    @abstractmethod
    def list_message_ids(self):
        """ List of message ids for all objects managed by this manager """


class TranslationManager(object):
    """ Collection of ``TranslationContextManager``s """

    def __init__(self):
        self._registry = {}

    def register(self, context_manager):
        context = context_manager.context
        if context in self._registry:
            raise KeyError(
                "ContextManager with context '{}' already registered".format(
                context)
            )
        self._registry[context] = context_manager

    def list_contexts_and_message_ids(self, **kwargs):
        for context, context_manager_cls in self._registry.iteritems():
            context_manager = context_manager_cls(**kwargs)
            for message_id in context_manager.list_message_ids():
                yield (context, message_id)


translation_manager = TranslationManager()
