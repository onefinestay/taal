from __future__ import absolute_import

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from taal.models import TranslationMixin
from taal.sqlalchemy import TranslatableString, get_context, get_message_id


Base = declarative_base()


class ConcreteTranslation(TranslationMixin, Base):
    __tablename__ = "test_translations"


class CustomFields(Base):
    __tablename__ = "test_fields"

    id = Column(Integer, primary_key=True)
    name = Column(TranslatableString(20))
    identifier = Column(String(20))


def create_translation(session, language, obj, field, translation_str):
    context = get_context(obj.__table__, field)
    message_id = get_message_id(obj)

    translation = ConcreteTranslation(
        context=context,
        message_id=message_id,
        language=language,
        translation=translation_str)
    session.add(translation)
    session.commit()
