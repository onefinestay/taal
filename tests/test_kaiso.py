from kaiso.attributes import Uuid, String
from kaiso.types import Entity
import pytest

from taal.kaiso import TypeTranslationContext


class Animal(Entity):
    id = Uuid(unique=True)
    name = String()


class Fish(Animal):
    pass


class TestKaiso(object):
    def _setup(self, storage):
        storage.save(Fish)

    @pytest.mark.usesfixtures('storage')
    def test_kaiso(self, storage):
        self._setup(storage)
        translation_context = TypeTranslationContext(storage)
        message_ids = set(translation_context.list_message_ids())
        assert message_ids == set(['Entity', 'Animal', 'Fish'])

    @pytest.mark.usefixtures('storage')
    def test_foo(self, storage):
        self._setup(storage)
