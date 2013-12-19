# coding: utf-8

from __future__ import absolute_import, unicode_literals

from taal import Translator

from tests.models import Model, Translation


def test_basic(session_cls):
    session_en = session_cls()
    translator_en = Translator(Translation, session_cls(), 'en')
    translator_en.bind(session_en)

    session_fr = session_cls()
    translator_fr = Translator(Translation, session_cls(), 'fr')
    translator_fr.bind(session_fr)

    model = Model(name='name')
    session_en.add(model)
    session_en.commit()

    # translate into fr
    translatable = model.name
    translatable.pending_value = 'namë_fr'
    translator_fr.save_translation(translatable)

    new_model = Model(name='name')
    session_en.add(new_model)
    session_en.commit()

    suggestion = translator_fr.suggest_translation(
        new_model.name, from_language='en', to_language='fr')

    assert suggestion == 'namë_fr'


def test_no_data(session):
    model = Model(name='foo')
    translator = Translator(Translation, session, '')
    assert translator.suggest_translation(model.name, 'en', 'fr') is None


def test_use_most_frequent(session_cls):
    session_en = session_cls()
    translator_en = Translator(Translation, session_cls(), 'en')
    translator_en.bind(session_en)

    session_fr = session_cls()
    translator_fr = Translator(Translation, session_cls(), 'fr')
    translator_fr.bind(session_fr)

    def add_with_translation(en, fr):
        model = Model(name=en)
        session_en.add(model)
        session_en.commit()

        # translate into fr
        translatable = model.name
        translatable.pending_value = fr
        translator_fr.save_translation(translatable)

    model = Model(name='a')
    session_en.add(model)
    session_en.commit()

    add_with_translation('a', '1')
    translator_fr.suggest_translation(model.name, 'en', 'fr') == '1'

    add_with_translation('a', '2')
    add_with_translation('a', '2')
    translator_fr.suggest_translation(model.name, 'en', 'fr') == '2'


def test_unknown_language(session_cls):
    session = session_cls()
    translator = Translator(Translation, session_cls(), 'en')
    translator.bind(session)

    model = Model(name='name')
    session.add(model)
    session.commit()

    assert translator.suggest_translation(model.name, 'en', 'foo') is None
    assert translator.suggest_translation(model.name, 'foo', 'en') is None
