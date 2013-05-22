from kaiso.attributes import Uuid, String
from kaiso.types import Entity
import pytest

from taal import translation_manager
from taal.kaiso import TypeTranslationContextManager


class Animal(Entity):
    id = Uuid(unique=True)
    name = String()


class Fish(Animal):
    pass


class TestKaiso(object):
    def _setup(self, storage):
        storage.save(Fish)

    @pytest.mark.usesfixtures('storage')
    def test_kaiso_context_manager(self, storage):
        self._setup(storage)
        translation_context = TypeTranslationContextManager(storage=storage)
        message_ids = set(translation_context.list_message_ids())
        assert message_ids == set(['Entity', 'Animal', 'Fish'])

    @pytest.mark.usefixtures('storage')
    def test_kaiso_translation_manager(self, storage):
        self._setup(storage)
        context_message_id_pairs = set(
            translation_manager.list_contexts_and_message_ids(
                storage=storage))
        assert context_message_id_pairs == set([
            ('_taal:kaiso_type', 'Entity'),
            ('_taal:kaiso_type', 'Animal'),
            ('_taal:kaiso_type', 'Fish'),
        ])
