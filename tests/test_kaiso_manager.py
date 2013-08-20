import pytest

from taal import TranslatableString, Translator
from taal.exceptions import NoTranslatorRegistered
from taal.kaiso.context_managers import TypeTranslationContextManager

from tests.kaiso import Fish
from tests.models import Translation, CustomFieldsEntity


class TestKaiso(object):
    # Couldn't figure out how to inject fixtures into setup_method
    def _setup(self, manager):
        manager.save(Fish)

    def test_labeled_hierarchy(self, session, translating_manager):
        manager = translating_manager

        self._setup(manager)
        translator = Translator(Translation, session, 'en')
        translator.bind(manager)

        hierarchy = manager.get_labeled_type_hierarchy()
        entity = next(hierarchy)

        assert isinstance(entity[1], TranslatableString)

    def test_translating_class_labels(self, session, translating_manager):
        manager = translating_manager

        self._setup(manager)
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

    def test_serialize(self, session, translating_manager):
        manager = translating_manager

        self._setup(manager)
        translator = Translator(Translation, session, 'en')
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
