import pytest

from taal import translation_manager
from taal.kaiso import TypeTranslationContextManager, patch_kaiso

from tests.kaiso import Fish


class TestKaiso(object):
    # Couldn't figure out how to inject fixtures into setup_method
    def _setup(self, storage):
        storage.save(Fish)

    @pytest.mark.usesfixtures('storage')
    def test_kaiso_context_manager(self, storage):
        self._setup(storage)
        context_manager = TypeTranslationContextManager(storage=storage)
        message_ids = set(context_manager.list_message_ids())
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

    @pytest.mark.usefixtures('storage')
    def test_kaiso_patching(self, storage):
        self._setup(storage)
        for entry in storage.get_type_hierarchy():
            assert len(entry) == 3
        with patch_kaiso():
            for entry in storage.get_type_hierarchy():
                assert len(entry) == 4
        for entry in storage.get_type_hierarchy():
            assert len(entry) == 3
