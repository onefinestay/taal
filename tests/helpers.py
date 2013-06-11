from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@contextmanager
def get_session():
    connection_string = pytest.config.getoption('db_uri')

    engine = create_engine(connection_string)
    session_cls = sessionmaker(bind=engine)

    session = session_cls()

    try:
        yield session
    finally:
        session.close()
        # make session unuseable
        session.__dict__ = {}
