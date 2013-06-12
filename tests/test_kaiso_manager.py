import pytest

from taal import TranslatableString
from taal.exceptions import NoTranslatorRegistered
from taal.kaiso.context_managers import TypeTranslationContextManager

from tests.helpers import get_translator
from tests.kaiso import Fish
from tests.models import ConcreteTranslation, CustomFieldsEntity


class TestKaiso(object):
    # Couldn't figure out how to inject fixtures into setup_method
    def _setup(self, manager):
        manager.save(Fish)

    def test_labeled_hierarchy(self, session, translating_manager):
        manager = translating_manager

        self._setup(manager)
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(manager)

            hierarchy = manager.get_labeled_type_hierarchy()
            entity = next(hierarchy)

            assert isinstance(entity[1], TranslatableString)

    def test_labeled_hierarchy_attributes(self, session, translating_manager):
        manager = translating_manager

        self._setup(manager)
        with get_translator(ConcreteTranslation, 'en') as translator:
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

    def test_translating_class_labels(self, session, translating_manager):
        manager = translating_manager

        self._setup(manager)
        with get_translator(ConcreteTranslation, 'en') as translator:
            translatable = TranslatableString(
                context=TypeTranslationContextManager.context,
                message_id='Entity', value='English Entity')

            translator.set_translation(translatable)
            translator.bind(manager)

            hierarchy = manager.get_labeled_type_hierarchy()
            entity = next(hierarchy)

            translated = translator.translate(entity[1])
            assert translated == 'English Entity'

    def test_serialize(self, session, translating_manager):
        manager = translating_manager

        self._setup(manager)
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(manager)

            obj = CustomFieldsEntity(id=1, name='English name')
            manager.save(obj)

            retrieved = manager.get(CustomFieldsEntity, id=1)

            serialized = manager.serialize(retrieved)
            translated = translator.translate(serialized)
            assert translated['name'] == 'English name'

    def test_missing_bind(self, session, translating_manager):
        manager = translating_manager
        obj = CustomFieldsEntity(id=1, name='English name')
        with pytest.raises(NoTranslatorRegistered):
            manager.save(obj)
