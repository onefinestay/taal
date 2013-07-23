from weakref import WeakKeyDictionary

from kaiso.persistence import Manager as KaisoManager, TypeSystem
from kaiso.types import get_type_id, PersistableType

from taal import TranslatableString as TaalTranslatableString
from taal.exceptions import NoTranslatorRegistered
from taal.kaiso import TranslatableString
from taal.kaiso.context_managers import (
    AttributeTranslationContextManager, TypeTranslationContextManager)
from taal.kaiso.types import get_context, get_message_id


translator_registry = WeakKeyDictionary()


def register_translator(owner, translator):
    translator_registry[owner] = translator


def get_translator(owner):
    try:
        return translator_registry[owner]
    except KeyError:
        raise NoTranslatorRegistered(
            "No translator registered for {}".format(owner))


def _label_attributes(type_id, attrs):
    labelled_attrs = []
    for attr in attrs:
        label = TaalTranslatableString(
            context=AttributeTranslationContextManager.context,
            message_id=AttributeTranslationContextManager.get_message_id(
                type_id, attr)
        )
        attr.label = label
        labelled_attrs.append(attr)
    return labelled_attrs


def _save_type_id(translator, cls):
    # until we can manage this better, save a placeholder translation
    # with blank language (and value) so the type shows up as in the list
    # of missing translations for all other languages

    # temporarily change the language of the translator
    # TODO: better handling of tasks like this
    original_language = translator.language
    translator.language = ''
    type_id = get_type_id(cls)
    translatable = TaalTranslatableString(
        context=TypeTranslationContextManager.context,
        message_id=type_id,
        pending_value='',
    )
    translator.save_translation(translatable)
    translator.language = original_language


def collect_translatables(manager, obj):
    """ collect translatables from obj

        may also mutate obj to replace translations with placeholders

        returns an iterable yielding the collecting translatables or None

        expects translator.save_translation or translator.delete_translations
        to be called for each collected translatable
    """

    translations = []
    descriptor = manager.type_registry.get_descriptor(type(obj))
    for attr_name, attr_type in descriptor.attributes.items():
        attr = getattr(obj, attr_name)
        if isinstance(attr_type, TranslatableString):
            translations.append((attr_name, attr))
            # TODO: something better than this workaround
            # what do we want in the db?
            setattr(obj, attr_name, None)

    def iter_translatables():
        message_id = get_message_id(manager, obj)
        for attr_name, attr in translations:
            context = get_context(manager, obj, attr_name)
            translatable = TaalTranslatableString(
                context, message_id, attr)
            yield translatable

    return iter_translatables()


class Manager(KaisoManager):
    def serialize(self, obj):
        message_id = get_message_id(self, obj)
        data = super(Manager, self).serialize(obj)
        descriptor = self.type_registry.get_descriptor(type(obj))
        for attr_name, attr_type in descriptor.attributes.items():
            if isinstance(attr_type, TranslatableString):
                context = get_context(self, obj, attr_name)
                data[attr_name] = TaalTranslatableString(
                    context, message_id)
        return data

    def save(self, obj):
        translatables = collect_translatables(self, obj)
        saved = super(Manager, self).save(obj)

        if isinstance(obj, TypeSystem):
            return saved

        translator = get_translator(self)

        if isinstance(obj, PersistableType):
            _save_type_id(translator, obj)

        for translatable in translatables:
            translator.save_translation(translatable)

        return saved

    def delete(self, obj):
        translatables = collect_translatables(self, obj)
        result = super(Manager, self).delete(obj)

        translator = get_translator(self)

        for translatable in translatables:
            translator.delete_translations(translatable)

        return result

    def get_labeled_type_hierarchy(self, start_type_id=None):
        type_hierarchy = super(
            Manager, self).get_type_hierarchy(start_type_id)

        for type_id, bases, attrs in type_hierarchy:
            label = TaalTranslatableString(
                context=TypeTranslationContextManager.context,
                message_id=type_id
            )
            yield (
                type_id, label, bases, _label_attributes(type_id, attrs))
