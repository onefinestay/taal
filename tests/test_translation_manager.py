import pytest

from taal import translation_manager, TranslationContextManager


@pytest.yield_fixture(autouse=True)
def reset_registry():
    registry = translation_manager._registry.copy()
    yield
    translation_manager._registry = registry


class NoContextManager(TranslationContextManager):
    pass


class Manager(TranslationContextManager):
    context = 'foo'


def test_requires_context():
    with pytest.raises(TypeError):
        NoContextManager()


def test_duplicate_registration():
    translation_manager.register(Manager)
    with pytest.raises(KeyError):
        translation_manager.register(Manager)
