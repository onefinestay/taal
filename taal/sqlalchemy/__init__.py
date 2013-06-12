from __future__ import absolute_import

from taal import Translator
from taal.sqlalchemy.events import register_session, register_translator
from taal.sqlalchemy.types import TranslatableString, make_from_obj

__all__ = ['TranslatableString', 'make_from_obj', 'register_for_translation']


def register_for_translation(session, translator_session, model, language):
    translator = Translator(model, translator_session, language)
    register_translator(session, translator)
    register_session(session)
    return translator
