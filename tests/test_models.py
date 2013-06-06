from __future__ import absolute_import

import pytest

from taal import Translator, TranslatableString

from tests.models import ConcreteTranslation
from tests.helpers import get_session


@pytest.mark.usefixtures('manager')
class TestModels(object):
    def test_create(self, session):
        translation = ConcreteTranslation(
            context='', message_id='', language='')
        session.add(translation)
        session.commit()

        assert session.query(ConcreteTranslation).count() == 1

    def test_repr(self, session):
        translatable = TranslatableString(
            context='my context', message_id='my message id')

        assert "my context" in repr(translatable)
        assert "my message id" in repr(translatable)

    def test_translate(self, session):
        translation = ConcreteTranslation(
            context='context', message_id='message_id',
            language='language', value='translation')
        session.add(translation)
        session.commit()

        translator = Translator(ConcreteTranslation, session, 'language')
        translatable = TranslatableString(
            context='context', message_id='message_id')

        translation = translator.translate(translatable)
        assert translation == 'translation'

    def test_translate_missing(self, session):
        translator = Translator(ConcreteTranslation, session, 'language')
        translatable = TranslatableString(
            context='context', message_id='message_id')

        with pytest.raises(KeyError):
            translator.translate(translatable)

    def test_translate_missing_ignore(self, session):
        translator = Translator(
            ConcreteTranslation, session, 'language', fail_if_missing=False)
        translatable = TranslatableString(
            context='context', message_id='message_id')

        translation = translator.translate(translatable)
        assert "Translation missing" in translation

    def test_translate_structure(self, session):
        translation = ConcreteTranslation(
            context='context', message_id='message_id',
            language='language', value='translation')
        session.add(translation)
        session.commit()

        translator = Translator(ConcreteTranslation, session, 'language')
        translatable = TranslatableString(
            context='context', message_id='message_id')

        structure = {
            'int': 1,
            'str': 'str',
            'list': [1, 'str', translatable],
            'translatable': translatable,
        }

        translation = translator.translate(structure)
        assert translation == {
            'int': 1,
            'str': 'str',
            'list': [1, 'str', 'translation'],
            'translatable': 'translation',
        }


@pytest.mark.usefixtures('manager')
class TestWriting(object):
    def test_set_translation(self, session):
        translator = Translator(ConcreteTranslation, session, 'language')
        params = {
            'context': 'context',
            'message_id': 'message_id',
        }
        translatable = TranslatableString(value='translation', **params)
        translator.set_translation(translatable)

        read_translatable = TranslatableString(**params)
        translation = translator.translate(read_translatable)
        assert translation == 'translation'

    def test_update_translation(self, session):
        translator = Translator(ConcreteTranslation, session, 'language')
        params = {
            'context': 'context',
            'message_id': 'message_id',
        }
        translatable = TranslatableString(value='translation', **params)
        translator.set_translation(translatable)

        with get_session() as new_session:
            new_translator = Translator(
                ConcreteTranslation, new_session, 'language')
            new_translatable = TranslatableString(
                value='new translation', **params)
            new_translator.set_translation(new_translatable)

        read_translatable = TranslatableString(**params)
        translation = translator.translate(read_translatable)
        assert translation == 'new translation'
        assert session.query(ConcreteTranslation).count() == 1
