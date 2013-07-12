from weakref import WeakKeyDictionary

from kaiso.persistence import Manager as KaisoManager

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

    def save_or_delete(self, obj, super_method, action):
        translations = []  # queue up and do after save
        descriptor = self.type_registry.get_descriptor(obj.__class__)
        for attr_name, attr_type in descriptor.attributes.items():
            attr = getattr(obj, attr_name)
            if isinstance(attr_type, TranslatableString):
                translations.append((attr_name, attr))
                # TODO: something better than this workaround
                # what do we want in the db?
                setattr(obj, attr_name, None)

        result = super_method(obj)

        if not translations:
            return result

        translator = get_translator(self)

        message_id = get_message_id(self, obj)
        for attr_name, attr in translations:
            context = get_context(self, obj, attr_name)
            translatable = TaalTranslatableString(
                context, message_id, attr)
            action_method = getattr(translator, action)
            action_method(translatable)
        return result

    def save(self, obj):
        super_method = super(Manager, self).save
        action = 'save_translation'
        return self.save_or_delete(obj, super_method, action)

    def delete(self, obj):
        super_method = super(Manager, self).delete
        action = 'delete_translations'
        return self.save_or_delete(obj, super_method, action)

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
