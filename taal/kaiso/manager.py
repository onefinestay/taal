from weakref import WeakKeyDictionary

from kaiso.persistence import Manager as KaisoManager

from taal import TranslatableString as TaalTranslatableString
from taal.kaiso import TranslatableString
from taal.kaiso.context_managers import (
    AttributeTranslationContextManager, TypeTranslationContextManager)
from taal.kaiso.types import get_context, get_message_id


translator_registry = WeakKeyDictionary()


def register_translator(owner, translator):
    translator_registry[owner] = translator


def get_translator(owner):
    return translator_registry[owner]


def _label_attributes(type_id, attrs):
    for attr in attrs:
        label = TaalTranslatableString(
            context=AttributeTranslationContextManager.context,
            message_id=AttributeTranslationContextManager.get_message_id(
                type_id, attr)
        )
        attr.label = label
        yield attr


class Manager(KaisoManager):
    def serialize(self, obj):
        message_id = get_message_id(self, obj)
        data = super(Manager, self).serialize(obj)
        descriptor = self.type_registry.get_descriptor(obj.__class__)
        for attr_name, attr_type in descriptor.attributes.items():
            if isinstance(attr_type, TranslatableString):
                context = get_context(self, obj, attr_name)
                data[attr_name] = TaalTranslatableString(
                    context, message_id)
        return data

    def save(self, obj):
        translations = []  # queue up and do after save
        descriptor = self.type_registry.get_descriptor(obj.__class__)
        for attr_name, attr_type in descriptor.attributes.items():
            attr = getattr(obj, attr_name)
            if isinstance(attr_type, TranslatableString):
                translations.append((attr_name, attr))
                # TODO: something better than this workaround
                # what do we want in the db?
                setattr(obj, attr_name, None)

        saved = super(Manager, self).save(obj)

        if not translations:
            return saved

        translator = get_translator(self)

        message_id = get_message_id(self, obj)
        for attr_name, attr in translations:
            context = get_context(self, obj, attr_name)
            translatable = TaalTranslatableString(
                context, message_id, attr)
            translator.set_translation(translatable)
        return saved

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
