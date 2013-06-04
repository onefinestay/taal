from __future__ import absolute_import

import json

import pytest
from kaiso.types import Entity
from kaiso.attributes import Integer

from taal import translation_manager, TranslatableString, Translator
from taal.kaiso import (
    TypeTranslationContextManager, get_context, get_message_id)

from tests.kaiso import Fish
from tests.models import (
    CustomFieldsEntity, ConcreteTranslation, create_translation_for_entity)


manager_fixture = pytest.mark.usesfixtures('manager')
fixture = pytest.mark.usesfixtures('session')


class TestKaiso(object):
    # Couldn't figure out how to inject fixtures into setup_method
    def _setup(self, manager):
        manager.save(Fish)

    def test_kaiso_context_manager(self, manager):
        self._setup(manager)
        context_manager = TypeTranslationContextManager(manager=manager)
        message_ids = set(context_manager.list_message_ids())
        assert message_ids == set(['Entity', 'Animal', 'Fish'])

    def test_kaiso_translation_manager(self, manager):
        self._setup(manager)
        context_message_id_pairs = set(
            translation_manager.list_contexts_and_message_ids(
                manager=manager))
        assert context_message_id_pairs == set([
            ('taal:kaiso_type', 'Entity'),
            ('taal:kaiso_type', 'Animal'),
            ('taal:kaiso_type', 'Fish'),
        ])


class MultipleUniques(Entity):
    id1 = Integer(unique=True, default=1)
    id2 = Integer(unique=True, default=1)


class TestFields(object):
    def test_field(self, manager):
        item = CustomFieldsEntity(id=0, identifier="foo")
        manager.save(item)

        retrieved = manager.get(CustomFieldsEntity, id=0)
        assert retrieved.identifier == "foo"

    def test_cant_set_translatable_field(self, manager):
        item = CustomFieldsEntity(name="foo")
        with pytest.raises(RuntimeError):
            manager.save(item)

    def test_context_message_id(self, session, manager):
        item = CustomFieldsEntity(id=0)
        manager.save(item)

        create_translation_for_entity(
            session, manager, 'english', item, 'name', 'English name')
        translation = session.query(ConcreteTranslation).one()
        expected_context = "taal:kaiso_field:CustomFieldsEntity:name"
        expected_message_id = json.dumps([("customfieldsentity", "id", 0)])

        assert translation.context == expected_context
        assert translation.message_id == expected_message_id

    def test_multiple_uniques(self, manager):
        item = MultipleUniques()
        manager.save(item)
        message_id = get_message_id(manager, item)
        expected_message_id = json.dumps([
            ("multipleuniques", "id1", 1),
            ("multipleuniques", "id2", 1),
        ])
        assert message_id == expected_message_id

    def test_get_translation(self, session, manager):
        item = CustomFieldsEntity()
        manager.save(item)

        create_translation_for_entity(
            session, manager, 'english', item, 'name', 'English name')

        context = get_context(manager, item, 'name')
        message_id = get_message_id(manager, item)
        translatable = TranslatableString(
            context=context, message_id=message_id)

        translator = Translator(ConcreteTranslation, session, 'english')
        translated_data = translator.translate(translatable)

        assert translated_data == 'English name'
