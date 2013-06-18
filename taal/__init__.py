""" Taal: Translations for SQLAlchemy and Kaiso models

    Store and manage translations using SQLAlchemy
"""

from __future__ import absolute_import

from abc import ABCMeta, abstractmethod, abstractproperty

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import tuple_

from taal.exceptions import BindError


try:
    VERSION = __import__('pkg_resources').get_distribution('taal').version
except:  # pragma: no cover
    VERSION = 'unknown'


class TranslatableString(object):
    """
    Placeholder for a string to be translated

    Holds metadata, ``context`` and ``message_id``, and optionally
    a string ``value``

    A ``TranslatableString`` with no ``message_id`` or ``value`` is
    considered empty (``is_unset``)
    """

    def __init__(self, context=None, message_id=None, value=None):
        self.context = context
        self.message_id = message_id
        self.value = value

    def is_unset(self):
        """ The "empty" TranslatableString """
        return (self.message_id is None and self.value is None)

    def __repr__(self):
        return "<TranslatableString: ({}, {}, {})>".format(
            self.context, self.message_id, self.value)

    def __eq__(self, other):
        self_dict = getattr(self, '__dict__', None)
        other_dict = getattr(other, '__dict__', None)
        return self_dict == other_dict


class Translator(object):
    """
    Manage a particular set of translations

    Given a sqlalchemy session, a model to store translations, and
    a language, bind a translator to a(n other) sqlalchemy session
    and/or a kaiso manager to get translation magic

    In addition to native data types, attributes will also include
    instances of ``TranslatableString``. A translator may subsequently
    be passed "structured" data (dicts, lists, tuples) containing
    translatable strings and translate to a particular language
    """

    def __init__(self, model, session, language, debug_output=False):
        self.model = model
        self.session = session
        self.language = language
        self.debug_output = debug_output

    def bind(self, target):
        """ register e.g. a sqlalchey session or a kaiso manager """
        from taal.kaiso import manager

        if isinstance(target, Session):
            from taal.sqlalchemy.events import (
                register_translator, register_session)
            register_translator(target, self)
            register_session(target)
        elif isinstance(target, manager.Manager):
            manager.register_translator(target, self)
        else:
            raise BindError("Unknown target {}".format(target))

    def _debug_message(self, translatable):
        return "[Translation missing ({}, {}, {})]".format(
            self.language, translatable.context, translatable.message_id)

    def _translate(self, translatable, cache):
        try:
            return cache[(translatable.context, translatable.message_id)]
        except KeyError:
            if self.debug_output:
                return self._debug_message(translatable)
            return None

    def translate(self, translatable, cache=None):
        """
        Translate ``TranslatableString`` by looking up a translation

        can also take a 'structure' (currently lists, tuples, and dicts)
        and recursively translate any TranslatableStrings found.
        """

        if cache is None:
            cache = self._prepare_cache(translatable)

        if isinstance(translatable, TranslatableString):
            return self._translate(translatable, cache)
        elif isinstance(translatable, dict):
            return dict(
                (key, self.translate(val, cache))
                for key, val in translatable.iteritems()
            )
        elif isinstance(translatable, list):
            return list(
                self.translate(item, cache)
                for item in translatable)
        elif isinstance(translatable, tuple):
            return tuple(
                self.translate(item, cache)
                for item in translatable)

        else:
            return translatable

    def _prepare_cache(self, translatable):
        """
        Bulk load translations required to translate a translatable
        'structure'
        """
        translatables = self._collect_translatables(translatable)
        if not translatables:
            return {}

        pks = [(t.context, t.message_id) for t in translatables]
        pk_filter = tuple_(self.model.context, self.model.message_id).in_(pks)
        translations = self.session.query(self.model).filter(
            self.model.language == self.language).filter(pk_filter).values(
                self.model.context, self.model.message_id, self.model.value)
        cache = {(t[0], t[1]): t[2] for t in translations}
        return cache

    def _collect_translatables(self, translatable, collection=None):
        """
        Run over a translatable 'structure' and collect any translatables
        These are then bulk loaded from the db
        """

        if collection is None:
            collection = []

        if isinstance(translatable, TranslatableString):
            collection.append(translatable)
        elif isinstance(translatable, dict):
            [self._collect_translatables(val, collection)
                for val in translatable.itervalues()]
        elif isinstance(translatable, list):
            [self._collect_translatables(item, collection)
                for item in translatable]
        elif isinstance(translatable, tuple):
            [self._collect_translatables(item, collection)
                for item in translatable]

        return collection

    def save_translation(self, translatable, commit=True):
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
    """ Knows all available ``message_id``\s for a given context """

    __metaclass__ = ABCMeta

    @abstractproperty
    def context(self):
        """ String used to identify translations managed by this manager """

    @abstractmethod
    def list_message_ids(self):
        """ List of message ids for all objects managed by this manager """


class TranslationManager(object):
    """ Collection of ``TranslationContextManager``\s """

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
