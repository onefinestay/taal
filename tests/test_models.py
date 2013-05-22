from contextlib import contextmanager

import pymysql
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from taal.models import TranslationMixin
from taal import Translator, TranslatableString


ECHO = False

pymysql.install_as_MySQLdb()

# engine = create_engine('sqlite:///:memory:', echo=True)
connection_string = 'mysql://127.0.0.1:33306/test_taal'


def drop_and_recreate_db():
    server, db_name = connection_string.rsplit('/', 1)
    engine = create_engine(server)
    query = 'DROP DATABASE {0}; CREATE DATABASE {0}'.format(db_name)
    engine.execute(query)


engine = create_engine(connection_string, echo=ECHO)
Base = declarative_base()
session_cls = sessionmaker(bind=engine)


@contextmanager
def Session():
    session = session_cls()
    try:
        yield session
    finally:
        session.close()


class ConcreteTranslation(TranslationMixin, Base):
    __tablename__ = "test_translations"


class TestModels(object):
    def setup_method(self, method):
        drop_and_recreate_db()
        Base.metadata.create_all(engine)

    def test_create(self):
        with Session() as session1:
            translation = ConcreteTranslation(
                context='', message_id='', language='')
            session1.add(translation)
            session1.commit()

        with Session() as session2:
            assert session2.query(ConcreteTranslation).count() == 1

    def test_translate(self):
        with Session() as session:
            translation = ConcreteTranslation(
                context='context', message_id='message_id',
                language='language', translation='translation')
            session.add(translation)
            session.commit()

            translator = Translator(ConcreteTranslation, session)
            translatable = TranslatableString(
                context='context', message_id='message_id')

            translation = translator.translate(translatable, 'language')
            assert translation == 'translation'

    def test_translate_structure(self):
        with Session() as session:
            translation = ConcreteTranslation(
                context='context', message_id='message_id',
                language='language', translation='translation')
            session.add(translation)
            session.commit()

            translator = Translator(ConcreteTranslation, session)
            translatable = TranslatableString(
                context='context', message_id='message_id')

            structure = {
                'int': 1,
                'str': 'str',
                'list': [1, 'str', translatable],
                'translatable': translatable,
            }

            translation = translator.translate(structure, 'language')
            assert translation == {
                'int': 1,
                'str': 'str',
                'list': [1, 'str', 'translation'],
                'translatable': 'translation',
            }
