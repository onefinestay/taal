import pytest

from taal import TranslatableString, Translator
from taal.exceptions import NoTranslatorRegistered
from taal.kaiso.context_managers import TypeTranslationContextManager

from tests.models import Translation, CustomFieldsEntity


def test_labeled_hierarchy(session, translating_type_heirarchy, bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translator.bind(manager)

    hierarchy = manager.get_labeled_type_hierarchy()
    entity = next(hierarchy)

    assert isinstance(entity[1], TranslatableString)


def test_labeled_hierarchy_attributes(session, translating_type_heirarchy,
                                      bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translator.bind(manager)

    hierarchy = manager.get_labeled_type_hierarchy()
    data = {}
    for type_id, label, bases, attrs in hierarchy:
        data[type_id] = {
            'label': label,
            'attrs': attrs,
        }

    animal = data['Animal']
    attrs = {attr.name: attr for attr in animal['attrs']}
    name_attr = attrs['name']
    assert isinstance(name_attr.label, TranslatableString)


def test_translating_class_labels(session, translating_type_heirarchy,
                                  bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translatable = TranslatableString(
        context=TypeTranslationContextManager.context,
        message_id='Entity', pending_value='English Entity')

    translator.save_translation(translatable)
    translator.bind(manager)

    hierarchy = manager.get_labeled_type_hierarchy()
    entity = next(hierarchy)

    translated = translator.translate(entity[1])
    assert translated == 'English Entity'


def test_serialize(session, translating_type_heirarchy, bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translator.bind(manager)

    obj = CustomFieldsEntity(id=1, name='English name')
    manager.save(obj)

    retrieved = manager.get(CustomFieldsEntity, id=1)

    serialized = manager.serialize(retrieved)
    translated = translator.translate(serialized)
    assert translated['name'] == 'English name'


def test_missing_bind(session, translating_manager):
    manager = translating_manager
    obj = CustomFieldsEntity(id=1, name='English name')
    with pytest.raises(NoTranslatorRegistered):
        manager.save(obj)
