from __future__ import absolute_import

from kaiso.exceptions import DeserialisationError
import pytest

from taal import TranslatableString, Translator
from taal.constants import PLACEHOLDER, PlaceholderValue
from taal.exceptions import NoTranslatorRegistered
from taal.kaiso.context_managers import TypeTranslationContextManager
from taal.kaiso.manager import collect_translatables
from taal.kaiso.types import get_context, get_message_id

from tests.models import Translation, CustomFieldsEntity


def test_labeled_hierarchy(session, translating_type_heirarchy, bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translator.bind(manager)

    hierarchy = manager.get_labeled_type_hierarchy()
    entity = next(hierarchy)

    assert isinstance(entity[1], TranslatableString)


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


def test_collect_translatables(bound_manager):
    manager = bound_manager

    obj = CustomFieldsEntity(id=1, name="value", extra1="", extra2=None)
    manager.save(CustomFieldsEntity)
    manager.save(obj)

    translatables = collect_translatables(manager, obj)

    expected_values = {
        "name": PLACEHOLDER,
        "extra1": PLACEHOLDER,
        "extra2": None
    }

    for translatable in translatables:
        attr_name = translatable.context.split(":")[-1]
        expected_value = expected_values.pop(attr_name)
        assert translatable.context == get_context(manager, obj, attr_name)
        assert translatable.message_id == get_message_id(manager, obj)
        assert translatable.pending_value == expected_value

    assert expected_values == {}


def test_serialize(session, translating_type_heirarchy, bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translator.bind(manager)

    obj = CustomFieldsEntity(id=1, name='English name', extra1="", extra2=None)
    manager.save(CustomFieldsEntity)
    manager.save(obj)

    retrieved = manager.get(CustomFieldsEntity, id=1)
    assert retrieved.name == PlaceholderValue
    assert retrieved.extra1 == PlaceholderValue
    assert retrieved.extra2 is None

    serialized = manager.serialize(retrieved)
    assert isinstance(serialized['name'], TranslatableString)
    assert isinstance(serialized['extra1'], TranslatableString)
    assert serialized['extra2'] is None

    translated = translator.translate(serialized)
    assert translated['name'] == 'English name'
    assert translated['extra1'] == ""
    assert translated['extra2'] is None


def test_deserialize_instance(
        session, translating_type_heirarchy, bound_manager):
    manager = bound_manager

    object_dict = {
        '__type__': 'CustomFieldsEntity',
        'id': 1,
        'name': 'English name',
        'extra1': None,
    }

    obj = manager.deserialize(object_dict)
    assert obj.id == 1
    assert obj.name == 'English name'
    assert obj.extra1 is None


def test_cannot_deserialize_without_type_key(bound_manager):
    manager = bound_manager

    object_dict = {
        'name': 'English name',
    }

    with pytest.raises(DeserialisationError):
        manager.deserialize(object_dict)


def test_deserialize_type(bound_manager):
    manager = bound_manager

    object_dict = {
        '__type__': 'PersistableType',
        'id': 'CustomFieldsEntity',
    }
    obj = manager.deserialize(object_dict)
    assert obj is CustomFieldsEntity


def test_save(session_cls, bound_manager):
    manager = bound_manager

    def check_value(obj, attr_name, expected_value):
        context = get_context(manager, obj, attr_name)
        assert session_cls().query(Translation).filter_by(
            context=context).one().value == expected_value

    manager.save(CustomFieldsEntity)

    obj = CustomFieldsEntity(id=1, name="value", extra1="", extra2=None)
    manager.save(obj)
    assert session_cls().query(Translation).count() == 2
    check_value(obj, "name", "value")
    check_value(obj, "extra1", "")

    obj.extra1 = "non-empty string"
    manager.save(obj)
    assert session_cls().query(Translation).count() == 2
    check_value(obj, "extra1", "non-empty string")

    obj.extra2 = "not null"
    manager.save(obj)
    assert session_cls().query(Translation).count() == 3
    check_value(obj, "extra2", "not null")

    obj.extra1 = ""
    manager.save(obj)
    assert session_cls().query(Translation).count() == 3

    obj.extra2 = None
    manager.save(obj)
    assert session_cls().query(Translation).count() == 2


def test_delete(session_cls, bound_manager):
    manager = bound_manager

    manager.save(CustomFieldsEntity)

    obj1 = CustomFieldsEntity(id=1, name="value", extra1="", extra2=None)
    obj2 = CustomFieldsEntity(id=2, name="value", extra1="", extra2=None)
    manager.save(obj1)
    manager.save(obj2)
    assert session_cls().query(Translation).count() == 4

    manager.delete(obj1)
    assert session_cls().query(Translation).count() == 2

    manager.delete(obj2)
    assert session_cls().query(Translation).count() == 0


def test_missing_bind(session, translating_manager):
    manager = translating_manager
    manager.save(CustomFieldsEntity)
    obj = CustomFieldsEntity(id=1, name='English name')
    with pytest.raises(NoTranslatorRegistered):
        manager.save(obj)


def test_serializing_type(translating_manager):
    # regression test
    data = translating_manager.serialize(CustomFieldsEntity)
    assert 'id' in data
