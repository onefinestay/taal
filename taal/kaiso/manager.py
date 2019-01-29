import copy
from weakref import WeakKeyDictionary

from kaiso.exceptions import DeserialisationError
from kaiso.persistence import Manager as KaisoManager
from kaiso.types import PersistableType, get_type_id

from taal.constants import PLACEHOLDER
from taal.exceptions import NoTranslatorRegistered
from taal.kaiso import TranslatableString, TYPE_CONTEXT
from taal.kaiso.types import get_context, get_message_id
from taal.translatablestring import (
    is_translatable_value,
    TranslatableString as TaalTranslatableString,
)


MISSING = object()
translator_registry = WeakKeyDictionary()


def register_translator(owner, translator):
    translator_registry[owner] = translator


def get_translator(owner):
    try:
        return translator_registry[owner]
    except KeyError:
        raise NoTranslatorRegistered(
            "No translator registered for {}".format(owner))


def iter_translatables(descriptor):
    """ yield translatable attributes given a descriptor """
    for attr_name, attr_type in descriptor.attributes.items():
        if isinstance(attr_type, TranslatableString):
            yield attr_name


def collect_translatables(manager, obj):
    """ Return translatables from ``obj``.

    Mutates ``obj`` to replace translations with placeholders.

    Expects translator.save_translation or translator.delete_translations
    to be called for each collected translatable.
    """
    if isinstance(obj, PersistableType):
        # object is a type; nothing to do
        return []

    translatables = []

    descriptor = manager.type_registry.get_descriptor(type(obj))
    message_id = get_message_id(manager, obj)

    for attr_name in iter_translatables(descriptor):
        attr = getattr(obj, attr_name)

        if is_translatable_value(attr):
            setattr(obj, attr_name, PLACEHOLDER)

        if isinstance(attr, TaalTranslatableString):
            # not changed since value was loaded, so don't collect for
            # updating the translations table
            continue

        context = get_context(manager, obj, attr_name)
        translatable = TaalTranslatableString(
            context, message_id, attr)
        translatables.append(translatable)

    return translatables


class Manager(KaisoManager):

    def serialize(self, obj, for_db=False):
        if for_db or type(obj) is PersistableType:
            return super(Manager, self).serialize(obj)

        message_id = get_message_id(self, obj)
        data = super(Manager, self).serialize(obj)
        descriptor = self.type_registry.get_descriptor(type(obj))
        for attr_name, attr_type in descriptor.attributes.items():
            if isinstance(attr_type, TranslatableString):
                value = data[attr_name]
                if is_translatable_value(value):
                    context = get_context(self, obj, attr_name)
                    data[attr_name] = TaalTranslatableString(
                        context, message_id)
        return data

    def deserialize(self, object_dict):
        # we don't need to do any translation here; we just need to
        # pop off any values for translatable fields during deserialization
        # and put them back afterwards

        try:
            type_id = object_dict['__type__']
        except KeyError:
            raise DeserialisationError(
                'properties "{}" missing __type__ key'.format(object_dict))

        if type_id == get_type_id(PersistableType):
            return super(Manager, self).deserialize(object_dict)

        descriptor = self.type_registry.get_descriptor_by_id(type_id)
        translatables = {}

        # deserialize a copy so we don't mutate object_dict
        object_dict_copy = copy.copy(object_dict)

        for attr_name, attr_type in descriptor.attributes.items():
            if isinstance(attr_type, TranslatableString):
                if attr_name not in object_dict_copy:
                    continue
                translatables[attr_name] = object_dict_copy.pop(attr_name)

        obj = super(Manager, self).deserialize(object_dict_copy)
        for attr_name, value in translatables.items():
            setattr(obj, attr_name, value)

        return obj

    def save(self, obj):
        translatables = collect_translatables(self, obj)
        result = super(Manager, self).save(obj)

        if translatables:
            translator = get_translator(self)
            for translatable in translatables:
                if is_translatable_value(translatable.pending_value):
                    translator.save_translation(translatable)
                else:
                    # delete all translations (in every language) if the
                    # value is None or the empty string
                    translator.delete_translations(translatable)

        return result

    def delete(self, obj):
        translatables = collect_translatables(self, obj)
        result = super(Manager, self).delete(obj)

        if translatables:
            translator = get_translator(self)
            for translatable in translatables:
                translator.delete_translations(translatable)

        return result

    def get_labeled_type_hierarchy(self, start_type_id=None):
        type_hierarchy = super(
            Manager, self).get_type_hierarchy(start_type_id)

        for type_id, bases, attrs in type_hierarchy:
            label = TaalTranslatableString(
                context=TYPE_CONTEXT,
                message_id=type_id
            )
            yield (type_id, label, bases, attrs)

    def change_instance_type(self, obj, type_id, updated_values=None):

        if updated_values is None:
            updated_values = {}

        updated_values = updated_values.copy()

        old_descriptor = self.type_registry.get_descriptor(type(obj))
        new_descriptor = self.type_registry.get_descriptor_by_id(type_id)

        old_message_id = get_message_id(self, obj)
        old_translatables = {}

        # collect any translatable fields on the original object
        # also, replace any values with placeholders for the super() call

        for attr_name in iter_translatables(old_descriptor):
            attr = getattr(obj, attr_name)
            if is_translatable_value(attr):
                setattr(obj, attr_name, PLACEHOLDER)
            context = get_context(self, obj, attr_name)
            translatable = TaalTranslatableString(
                context, old_message_id, attr)
            old_translatables[attr_name] = translatable

        new_translatables = {}

        # collect any translatable fields from the new type
        # also, replace any values in updated_values with placeholders
        # for the super() call

        # note that we can't collect the context/message_id until after
        # we call super(), since they may be about to change
        # (context will definitely change, and message_id might, if we add or
        # remove unique attributes)

        for attr_name in iter_translatables(new_descriptor):
            attr = updated_values.get(attr_name, MISSING)
            if attr is None:
                continue
            if attr is MISSING:
                attr = None

            if is_translatable_value(attr):
                updated_values[attr_name] = PLACEHOLDER
            translatable = TaalTranslatableString(
                None, None, attr)
            new_translatables[attr_name] = translatable

        new_obj = super(Manager, self).change_instance_type(
            obj, type_id, updated_values)

        # we are now able to fill in context/message_id for the new object

        new_message_id = get_message_id(self, new_obj)
        for attr_name, translatable in new_translatables.items():
            translatable.message_id = new_message_id
            translatable.context = get_context(self, new_obj, attr_name)

        to_delete = set(old_translatables) - set(new_translatables)
        to_rename = set(old_translatables) & set(new_translatables)
        to_add = set(new_translatables) - set(old_translatables)

        translator = get_translator(self)

        for key in to_delete:
            translatable = old_translatables[key]
            translator.delete_translations(translatable)

        for key in to_rename:
            old_translatable = old_translatables[key]
            new_translatable = new_translatables[key]
            translator.move_translations(old_translatable, new_translatable)
            if new_translatable.pending_value is not None:
                # updated_values contained a key for a field already existing
                # on the old type. save the updated translation
                translator.save_translation(new_translatable)

        for key in to_add:
            translatable = new_translatables[key]
            if translatable.pending_value is not None:
                translator.save_translation(translatable)

        return new_obj
