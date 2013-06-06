from __future__ import absolute_import

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from kaiso.types import Entity
from kaiso.attributes import Integer as KaisoInteger, String as KaisoString

from taal.models import TranslationMixin
from taal import kaiso as taal_kaiso, sqlalchemy as taal_sqlalchemy


Base = declarative_base()


class ConcreteTranslation(TranslationMixin, Base):
    __tablename__ = "test_translations"


class CustomFields(Base):
    __tablename__ = "test_fields"

    id = Column(Integer, primary_key=True)
    name = Column(taal_sqlalchemy.TranslatableString(20))
    identifier = Column(String(20))


class CustomFieldsEntity(Entity):
    id = KaisoInteger(unique=True)
    name = taal_kaiso.TranslatableString()  # human readable
    identifier = KaisoString()


def _create_translation(
        session, language, context, message_id, translation_str):
    translation = ConcreteTranslation(
        context=context,
        message_id=message_id,
        language=language,
        value=translation_str)
    session.add(translation)
    session.commit()


def create_translation_for_model(
        session, language, obj, field, translation_str):
    context = taal_sqlalchemy.get_context(obj, field)
    message_id = taal_sqlalchemy.get_message_id(obj)
    return _create_translation(
        session, language, context, message_id, translation_str)


def create_translation_for_entity(
        session, manager, language, obj, field, translation_str):
    context = taal_kaiso.get_context(manager, obj, field)
    message_id = taal_kaiso.get_message_id(manager, obj)
    return _create_translation(
        session, language, context, message_id, translation_str)
