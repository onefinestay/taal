import pytest

from taal import translation_manager, TranslationContextManager


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
