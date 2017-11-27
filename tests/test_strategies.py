# coding: utf-8

from __future__ import absolute_import, unicode_literals

import pytest

from taal import Translator, TRANSLATION_MISSING
from taal.translatablestring import TranslatableString

from tests.models import Translation

SAMPLE_CONTEXT = 'context ಠ_ಠ'
SAMPLE_MESSAGE_ID = 'message_id ಠ_ಠ'
SAMPLE_LANGUAGE = 'language ಠ_ಠ'


@pytest.mark.usefixtures('manager')
class TestStrategies(object):
    def test_none_value(self, session):
        translator = Translator(Translation, session, SAMPLE_LANGUAGE)
        translatable = TranslatableString(
            context=SAMPLE_CONTEXT, message_id=SAMPLE_MESSAGE_ID)

        translation = translator.translate(translatable)
        translation is None

    def test_sentinel_value(self, session):
        translator = Translator(
            Translation,
            session,
            SAMPLE_LANGUAGE,
            strategy=Translator.strategies.SENTINEL_VALUE
        )
        translatable = TranslatableString(
            context=SAMPLE_CONTEXT, message_id=SAMPLE_MESSAGE_ID)

        translation = translator.translate(translatable)
        assert translation is TRANSLATION_MISSING

    def test_sentinel_value_repr(self):
        assert 'TranslationMissing' in repr(TRANSLATION_MISSING)
        assert 'sentinel' in repr(TRANSLATION_MISSING)

    def test_debug_value(self, session):
        translator = Translator(
            Translation,
            session,
            SAMPLE_LANGUAGE,
            strategy=Translator.strategies.DEBUG_VALUE
        )
        translatable = TranslatableString(
            context=SAMPLE_CONTEXT, message_id=SAMPLE_MESSAGE_ID)

        translation = translator.translate(translatable)
        assert "[Translation missing" in translation

    def test_en_fallback(self, session):
        translation = Translation(
            context=SAMPLE_CONTEXT,
            message_id=SAMPLE_MESSAGE_ID,
            language='en',
            value='en fallback',
        )
        session.add(translation)
        session.commit()
        translator = Translator(
            Translation,
            session,
            SAMPLE_LANGUAGE,
            strategy=Translator.strategies.EN_FALLBACK,
        )

        translatable = TranslatableString(
            context=SAMPLE_CONTEXT, message_id=SAMPLE_MESSAGE_ID)

        translation = translator.translate(translatable)
        assert translation == 'en fallback'

    def test_override(self, session):
        translator = Translator(
            Translation,
            session,
            SAMPLE_LANGUAGE,
            strategy=Translator.strategies.DEBUG_VALUE
        )
        translatable = TranslatableString(
            context=SAMPLE_CONTEXT, message_id=SAMPLE_MESSAGE_ID)

        translation = translator.translate(
            translatable, strategy=translator.strategies.SENTINEL_VALUE)
        assert translation is TRANSLATION_MISSING

    def test_dont_save_debug_translation(self, session):
        translator = Translator(
            Translation,
            session,
            SAMPLE_LANGUAGE,
            strategy=Translator.strategies.DEBUG_VALUE
        )

        translatable = TranslatableString(
            context=SAMPLE_CONTEXT, message_id=SAMPLE_MESSAGE_ID)
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
                strategy='invalid ಠ_ಠ',
            )
        assert 'Invalid strategy `invalid ಠ_ಠ`' in unicode(exc)

    def test_invalid_override(self):
        translator = Translator(
            Translation,
            session=None,
            language=None,
        )
        with pytest.raises(ValueError) as exc:
            translator.translate(None, strategy='invalid ಠ_ಠ')
        assert 'Invalid strategy `invalid ಠ_ಠ`' in unicode(exc)
