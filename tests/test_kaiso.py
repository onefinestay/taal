import json

import pytest

from taal import translation_manager, TranslatableString, Translator
from taal.kaiso import (
    TypeTranslationContextManager, get_type_hierarchy, get_context,
    get_message_id)

from tests.kaiso import Fish
from tests.models import (
    CustomFieldsEntity, ConcreteTranslation, create_translation_for_entity)


storage_fixture = pytest.mark.usesfixtures('storage')
fixture = pytest.mark.usesfixtures('session')


class TestKaiso(object):
    # Couldn't figure out how to inject fixtures into setup_method
    def _setup(self, storage):
        storage.save(Fish)

    def test_kaiso_context_manager(self, storage):
        self._setup(storage)
        context_manager = TypeTranslationContextManager(storage=storage)
        message_ids = set(context_manager.list_message_ids())
        assert message_ids == set(['Entity', 'Animal', 'Fish'])

    def test_kaiso_translation_manager(self, storage):
        self._setup(storage)
        context_message_id_pairs = set(
            translation_manager.list_contexts_and_message_ids(
                storage=storage))
        assert context_message_id_pairs == set([
            ('taal:kaiso_type', 'Entity'),
            ('taal:kaiso_type', 'Animal'),
            ('taal:kaiso_type', 'Fish'),
        ])

    def test_kaiso_patching(self, storage):
        self._setup(storage)
        for entry in storage.get_type_hierarchy():
            assert len(entry) == 3
        for entry in get_type_hierarchy(storage):
            assert len(entry) == 4


class TestFields(object):
    def test_field(self, storage):
        item = CustomFieldsEntity(id=0, identifier="foo")
        storage.save(item)

        retrieved = storage.get(CustomFieldsEntity, id=0)
        assert retrieved.identifier == "foo"

    def test_cant_set_translatable_field(self, storage):
        item = CustomFieldsEntity(name="foo")
        with pytest.raises(RuntimeError):
            storage.save(item)

    def test_context_message_id(self, session, storage):
        item = CustomFieldsEntity(id=0)
        storage.save(item)

        create_translation_for_entity(
            session, 'english', item, 'name', 'English name')
        translation = session.query(ConcreteTranslation).one()
        expected_context = "taal:kaiso_field:CustomFieldsEntity:name"
        expected_message_id = json.dumps([("customfieldsentity", "id", 0)])

        assert translation.context == expected_context
        assert translation.message_id == expected_message_id

    def test_get_translation(self, session, storage):
        item = CustomFieldsEntity()
        storage.save(item)

        create_translation_for_entity(
            session, 'english', item, 'name', 'English name')

        context = get_context(item, 'name')
        message_id = get_message_id(item)
        translatable = TranslatableString(
            context=context, message_id=message_id)

        translator = Translator(ConcreteTranslation, session, 'english')
        translated_data = translator.translate(translatable)

        assert translated_data == 'English name'
