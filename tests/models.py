from __future__ import absolute_import

from sqlalchemy import (
    Column, Integer as SaInteger, String as SaString, Text, ForeignKey)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from kaiso.types import Entity
from kaiso.attributes import Integer as KaisoInteger, String as KaisoString

from taal.models import TranslationMixin
from taal import kaiso as taal_kaiso, sqlalchemy as taal_sqlalchemy
from taal.kaiso import types as taal_kaiso_types
from taal.sqlalchemy import types as taal_sqlalchemy_types


Base = declarative_base()


class Translation(TranslationMixin, Base):
    __tablename__ = "translations"


class CustomFieldsEntity(Entity):
    id = KaisoInteger(unique=True)
    identifier = KaisoString()
    name = taal_kaiso.TranslatableString()
    extra = taal_kaiso.TranslatableString()
    null = taal_kaiso.TranslatableString()


class NoCustomFieldsEntity(Entity):
    id = KaisoInteger(unique=True)
    identifier = KaisoString()


class MultipleUniques(Entity):
    id1 = KaisoInteger(unique=True, default=1)
    id2 = KaisoInteger(unique=True, default=1)


class InheritedUniques(MultipleUniques):
    id3 = KaisoInteger(unique=True, default=1)


class Parent(Base):
    __tablename__ = "test_parent"

    id = Column(SaInteger, primary_key=True)
    name = Column(taal_sqlalchemy.TranslatableString(20))
    identifier = Column(SaString(20))


class Child(Base):
    __tablename__ = "test_child"

    id = Column(SaInteger, primary_key=True)
    name = Column(taal_sqlalchemy.TranslatableString(20))
    identifier = Column(SaString(20))
    parent_id = Column(SaInteger, ForeignKey('test_parent.id'))
    parent = relationship('Parent', backref='children')


class Model(Base):
    __tablename__ = "models"

    id = Column(SaInteger, primary_key=True)
    name = Column(taal_sqlalchemy.TranslatableString)
    identifier = Column(Text)


class RequiredModel(Base):
    __tablename__ = "requiredmodels"

    id = Column(SaInteger, primary_key=True)
    name = Column(taal_sqlalchemy.TranslatableString, nullable=False)
    identifier = Column(Text)


# Consider moving to the TranslationContextManager
def _create_translation(
        session, language, context, message_id, translation_str):
    translation = Translation(
        context=context,
        message_id=message_id,
        language=language,
        value=translation_str)
    session.add(translation)
    session.commit()


def create_translation_for_model(
        session, language, obj, field, translation_str):
    context = taal_sqlalchemy_types.get_context(obj, field)
    message_id = taal_sqlalchemy_types.get_message_id(obj)
    return _create_translation(
        session, language, context, message_id, translation_str)


def create_translation_for_entity(
        session, manager, language, obj, field, translation_str):
    context = taal_kaiso_types.get_context(manager, obj, field)
    message_id = taal_kaiso_types.get_message_id(manager, obj)
    return _create_translation(
        session, language, context, message_id, translation_str)
