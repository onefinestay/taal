import pymysql
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from taal.models import TranslationMixin

pymysql.install_as_MySQLdb()

# engine = create_engine('sqlite:///:memory:', echo=True)
connection_string = 'mysql://127.0.0.1:33306/test_taal'

def drop_and_recreate_db():
    server, db_name = connection_string.rsplit('/', 1)
    engine = create_engine(server)
    query = 'DROP DATABASE {0}; CREATE DATABASE {0}'.format(db_name)
    engine.execute(query)


engine = create_engine(connection_string, echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class ConcreteTranslation(TranslationMixin, Base):
    __tablename__ = "test_translations"


def test_create():
    drop_and_recreate_db()
    Base.metadata.create_all(engine)
    session = Session()
    translation = ConcreteTranslation(
        context='', message_id='', language='')
    session.add(translation)
    session.commit()

    session2 = Session()
    assert session2.query(ConcreteTranslation).count() == 1
