from __future__ import absolute_import

import pytest
from sqlalchemy.exc import StatementError

from taal import Translator, TranslatableString
from taal.sqlalchemy import get_context, get_message_id
from tests.models import (
    CustomFields, ConcreteTranslation, create_translation_for_model)


fixture = pytest.mark.usesfixtures('session')


def test_field(session):
    model = CustomFields(identifier="foo")
    session.add(model)
    session.commit()

    retrieved = session.query(CustomFields).get(model.id)
    assert retrieved.identifier == "foo"


def test_cant_set_translatable_field(session):
    model = CustomFields(name="foo")
    session.add(model)
    with pytest.raises(StatementError):
        session.commit()


def test_get_translation(session):
    model = CustomFields()
    session.add(model)
    session.commit()

    create_translation_for_model(
        session, 'english', model, 'name', 'English name')

    context = get_context(CustomFields, 'name')
    message_id = get_message_id(model)
    translatable = TranslatableString(context=context, message_id=message_id)

    translator = Translator(ConcreteTranslation, session, 'english')
    translated_data = translator.translate(translatable)

    assert translated_data == 'English name'
