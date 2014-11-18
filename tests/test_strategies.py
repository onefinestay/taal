from __future__ import absolute_import

import pytest

from taal import Translator, TranslatableString, TRANSLATION_MISSING

from tests.models import Translation


@pytest.mark.usefixtures('manager')
class TestStrategies(object):
    def test_none_value(self, session):
        translator = Translator(Translation, session, 'language')
        translatable = TranslatableString(
            context='context', message_id='message_id')

        translation = translator.translate(translatable)
        translation is None

    def test_sentinel_value(self, session):
        translator = Translator(
            Translation,
            session,
            'language',
            strategy=Translator.strategies.SENTINEL_VALUE
        )
        translatable = TranslatableString(
            context='context', message_id='message_id')

        translation = translator.translate(translatable)
        assert translation is TRANSLATION_MISSING

    def test_sentinel_value_repr(self):
        assert 'TranslationMissing' in repr(TRANSLATION_MISSING)
        assert 'sentinel' in repr(TRANSLATION_MISSING)

    def test_debug_value(self, session):
        translator = Translator(
            Translation,
            session,
            'language',
            strategy=Translator.strategies.DEBUG_VALUE
        )
        translatable = TranslatableString(
            context='context', message_id='message_id')

        translation = translator.translate(translatable)
        assert "[Translation missing" in translation

    def test_override(self, session):
        translator = Translator(
            Translation,
            session,
            'language',
            strategy=Translator.strategies.DEBUG_VALUE
        )
        translatable = TranslatableString(
            context='context', message_id='message_id')

        translation = translator.translate(
            translatable, strategy=translator.strategies.SENTINEL_VALUE)
        assert translation is TRANSLATION_MISSING

    def test_dont_save_debug_translation(self, session):
        translator = Translator(
            Translation,
            session,
            'language',
            strategy=Translator.strategies.DEBUG_VALUE
        )

        translatable = TranslatableString(
            context='context', message_id='message_id')
        debug_value = translator._get_debug_translation(translatable)
        translatable.pending_value = debug_value

        translator.save_translation(translatable)

        assert session.query(Translation).count() == 0

    def test_invalid(self):
        with pytest.raises(ValueError) as exc:
            Translator(
                Translation,
                session=None,
                language=None,
                strategy='invalid',
            )
        assert 'Invalid strategy `invalid`' in str(exc)

    def test_invalid_override(self):
        translator = Translator(
            Translation,
            session=None,
            language=None,
        )
        with pytest.raises(ValueError) as exc:
            translator.translate(None, strategy='invalid')
        assert 'Invalid strategy `invalid`' in str(exc)
