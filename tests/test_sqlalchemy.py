from __future__ import absolute_import

import pytest
from sqlalchemy import Column, Text, Integer
from sqlalchemy.exc import OperationalError, StatementError
from sqlalchemy.ext.declarative import declarative_base

# from taal.models import TranslationMixin
from taal import Translator, TranslatableString
from tests.models import Model, RequiredModel, Translation, Parent, Child
from taal.sqlalchemy.events import flush_log, load
from taal.sqlalchemy.types import make_from_obj, NotNullValue


Base = declarative_base()


# initilisation

def test_init_none():
    instance = Model()
    assert instance.name is None


def test_init_value():
    instance = Model(name='name')
    assert isinstance(instance.name, TranslatableString)
    assert instance.name.pending_value == 'name'


@pytest.mark.parametrize(("first", "second"), [
    (None, None),
    (None, 'other'),
    ('name', None),
    ('name', 'other'),
])
def test_set_from_to(first, second):
    instance = Model(name=first)
    instance.name = second
    if second is None:
        assert instance.name is None
    else:
        assert isinstance(instance.name, TranslatableString)
        assert instance.name.pending_value == second


def test_set_from_other_instance():
    instance1 = Model(name='name')
    instance2 = Model(name=instance1.name)
    assert isinstance(instance2.name, TranslatableString)
    assert instance2.name.pending_value == 'name'


def test_set_from_other_instance_and_commit(bound_session):
    instance1 = Model(name='name')
    instance2 = Model(name=instance1.name)
    assert isinstance(instance2.name, TranslatableString)
    assert instance2.name.pending_value == 'name'
    bound_session.add(instance1)
    bound_session.add(instance2)
    bound_session.commit()


# basic persistence

def test_save_none(bound_session):
    instance = Model()
    bound_session.add(instance)
    bound_session.commit()
    assert instance.name is None


def test_save_value(bound_session):
    instance = Model(name='name')
    bound_session.add(instance)
    bound_session.commit()
    assert isinstance(instance.name, TranslatableString)
    assert instance.name.pending_value is None


@pytest.mark.parametrize(("first", "second"), [
    (None, None),
    (None, 'other'),
    ('name', None),
    ('name', 'other'),
])
def test_modify_from_to(bound_session, first, second):
    instance = Model(name=first)
    bound_session.add(instance)
    bound_session.commit()
    instance.name = second
    bound_session.commit()
    if second is None:
        assert instance.name is None
    else:
        assert isinstance(instance.name, TranslatableString)
        assert instance.name.pending_value is None


@pytest.mark.parametrize("value", [None, 'name', ])
def test_refresh(bound_session, session_cls, value):
    instance = Model(name=value)
    bound_session.add(instance)
    bound_session.commit()
    pk = instance.id

    instance = bound_session.query(Model).get(pk)
    if value is None:
        assert instance.name is None
    else:
        assert isinstance(instance.name, TranslatableString)


@pytest.mark.parametrize("value", [None, 'name', ])
def test_load(session, session_cls, value):
    instance = Model(name=value)
    translator = Translator(Translation, session_cls(), 'language')
    translator.bind(session)
    session.add(instance)
    session.commit()
    pk = instance.id

    # make a new session
    session = session_cls()
    translator.bind(session)
    instance = session.query(Model).get(pk)
    if value is None:
        assert instance.name is None
    else:
        assert isinstance(instance.name, TranslatableString)


@pytest.mark.parametrize("initial", [None, 'name', ])
def test_bulk_update_to_value(bound_session, initial):
    instance = Model(name=initial)
    bound_session.add(instance)
    bound_session.commit()

    with pytest.raises(StatementError):
        bound_session.query(Model).update({'name': 'name'})


def test_bulk_update_to_none(bound_session):
    # not yet supported
    instance = Model(name='name')
    bound_session.add(instance)
    bound_session.commit()

    with pytest.raises(RuntimeError):
        bound_session.query(Model).update({'name': None})


@pytest.mark.parametrize("initial", [None, 'name', ])
def test_flushing(bound_session, session_cls, initial):
    instance = Model(name=initial)
    bound_session.add(instance)
    bound_session.flush()

    if initial is None:
        assert instance.name is None
    else:
        assert isinstance(instance.name, TranslatableString)


@pytest.mark.parametrize(("first", "second"), [
    (None, None),
    (None, 'other'),
    ('name', None),
    ('name', 'other'),
])
def test_rollback(bound_session, first, second):
    instance = Model(name=first)
    bound_session.add(instance)
    bound_session.commit()
    instance.name = second
    if second is None:
        assert instance.name is None
    else:
        assert isinstance(instance.name, TranslatableString)
        assert instance.name.pending_value == second
    bound_session.rollback()
    if first is None:
        assert instance.name is None
    else:
        assert isinstance(instance.name, TranslatableString)
        assert instance.name.pending_value is None


class TestSavepoints(object):
    def test_verify(self, session, session_cls):
        # check the test setup works
        translator = Translator(Translation, session_cls(), 'language')
        translator.bind(session)

        assert session not in flush_log
        assert translator.session not in flush_log

        instance1 = Model(name='instance 1')
        session.add(instance1)

        session.flush()
        assert session in flush_log
        assert len(flush_log[session]) == 1
        session.commit()
        assert session not in flush_log

        instance2 = Model(name='instance 2')
        session.add(instance2)
        session.commit()
        assert session not in flush_log
        assert translator.session.query(Translation).count() == 2

    def test_savepoints(self, session, session_cls):
        translator = Translator(Translation, session_cls(), 'language')
        translator.bind(session)

        instance1 = Model(name='instance 1')
        session.add(instance1)

        session.begin_nested()

        instance2 = Model(name='instance 2')
        session.add(instance2)
        session.flush()
        assert session in flush_log
        assert len(flush_log[session]) == 2

        session.rollback()
        session.commit()

        assert session.query(Model).count() == 1
        assert translator.session.query(Translation).count() == 1


def test_refresh_with_relationship(bound_session):
    """ regression: refreshing attribute that isn't a column name """
    parent = Parent()
    child = Child(parent=parent)
    bound_session.add(child)
    bound_session.commit()

    assert parent.children == [child]


def test_merge_from_other_session(session_cls):
    """ regression test """
    session1 = session_cls()
    session2 = session_cls()

    translator = Translator(Translation, session_cls(), 'language')
    translator.bind(session1)
    translator.bind(session2)

    instance = Model(name='name')
    session1.add(instance)
    session1.commit()

    session2.merge(instance)


def test_dirty_but_not_modified(bound_session):
    instance = Model(identifier="foo")
    bound_session.add(instance)
    bound_session.commit()

    # trigger refresh
    assert instance.identifier
    instance.identifier = "foo"
    bound_session.flush()


@pytest.mark.parametrize(("first", "second"), [
    (None, None),
    (None, 'other'),
    ('name', None),
    ('name', 'other'),
])
def test_removing_translations(session, session_cls, first, second):
    translator = Translator(Translation, session_cls(), 'language')
    translator.bind(session)
    instance = Model(name=first)
    session.add(instance)
    session.commit()

    if first is None:
        assert translator.session.query(Translation).count() == 0
    else:
        assert translator.session.query(Translation).count() == 1

    instance.name = second
    session.commit()

    if second is None:
        assert translator.session.query(Translation).count() == 0
    else:
        assert translator.session.query(Translation).count() == 1


def test_deleting(session, session_cls):
    translator = Translator(Translation, session_cls(), 'language')
    translator.bind(session)
    instance = Model(name='name')
    assert translator.session.query(Translation).count() == 0

    session.add(instance)
    assert translator.session.query(Translation).count() == 0
    session.commit()
    assert translator.session.query(Translation).count() == 1

    session.delete(instance)
    assert translator.session.query(Translation).count() == 1
    session.rollback()
    assert translator.session.query(Translation).count() == 1
    session.commit()
    assert translator.session.query(Translation).count() == 1

    session.delete(instance)
    assert translator.session.query(Translation).count() == 1
    session.commit()
    assert translator.session.query(Translation).count() == 0


def test_unbound_session_errors(session):
    instance = Model(name='name')
    session.add(instance)
    with pytest.raises(StatementError):
        session.commit()


def test_reload_noop(bound_session):
    """ regression test. triggers `refresh` with `attrs=None` """
    instance = Model(name='name')
    bound_session.add(instance)
    bound_session.commit()
    bound_session.refresh(instance)


class TestMultipleLanguages(object):
    def test_values(self, session_cls):
        session1 = session_cls()
        translator1 = Translator(Translation, session_cls(), 'language1')
        translator1.bind(session1)

        session2 = session_cls()
        translator2 = Translator(Translation, session_cls(), 'language2')
        translator2.bind(session2)

        instance = Model(name='name')
        session1.add(instance)
        session1.commit()
        pk = instance.id

        loaded = session2.query(Model).get(pk)
        assert loaded.name is not None

        instance.name = None
        session1.commit()

        session2.rollback()  # expire isn't enough to trigger reloading
        assert loaded.name is None
        assert translator1.session.query(Translation).count() == 0

    def test_delete_on_none(self, session, session_cls):
        session1 = session_cls()
        translator1 = Translator(Translation, session_cls(), 'language1')
        translator1.bind(session1)

        session2 = session_cls()
        translator2 = Translator(Translation, session_cls(), 'language2')
        translator2.bind(session2)

        instance = Model(id=1)
        session.add(instance)
        session.commit()

        instance = session1.query(Model).get(1)
        instance.name = 'name'
        session1.commit()

        instance = session2.query(Model).get(1)
        instance.name = 'name'
        session2.commit()

        assert translator1.session.query(Translation).count() == 2
        instance.name = None
        assert translator1.session.query(Translation).count() == 2
        session2.commit()

        translator1.session.rollback()  # expire caches
        assert translator1.session.query(Translation).count() == 0

    def test_delete_on_delete(self, session, session_cls):
        session1 = session_cls()
        translator1 = Translator(Translation, session_cls(), 'language1')
        translator1.bind(session1)

        session2 = session_cls()
        translator2 = Translator(Translation, session_cls(), 'language2')
        translator2.bind(session2)

        instance = Model(id=1)
        session.add(instance)
        session.commit()

        instance = session1.query(Model).get(1)
        instance.name = 'name'
        session1.commit()

        instance = session2.query(Model).get(1)
        instance.name = 'name'
        session2.commit()

        assert translator1.session.query(Translation).count() == 2
        session2.delete(instance)
        assert translator1.session.query(Translation).count() == 2
        session2.commit()

        translator1.session.rollback()  # expire caches
        assert translator1.session.query(Translation).count() == 0


def test_set_from_other_model(session, session_cls):
    model1 = Model(name='name')
    model2 = RequiredModel(name=model1.name)
    translator = Translator(Translation, session_cls(), 'language')
    translator.bind(session)
    session.add(model1)
    session.add(model2)
    session.commit()

    assert translator.session.query(
        Translation.context).distinct().count() == 2


def test_corrupt_db(session, session_cls):
    class CorruptModel(Base):
        __tablename__ = "models"

        id = Column(Integer, primary_key=True)
        name = Column(Text)
        identifier = Column(Text)

    corrupt = CorruptModel(id=1, name='name')
    session.add(corrupt)
    session.commit()

    translator = Translator(Translation, session_cls(), 'language')
    translator.bind(session)
    with pytest.raises(RuntimeError):
        session.query(Model).get(1)


def test_query_values(session_cls):
    session1 = session_cls()
    session2 = session_cls()

    translator = Translator(Translation, session_cls(), 'language')
    translator.bind(session1)
    translator.bind(session2)
    model = Model(name='name')
    session1.add(model)
    session1.commit()

    (value,) = session2.query(Model.name).one()
    assert value == NotNullValue


def test_make_from_obj_error():
    instance = Model(name='name')
    with pytest.raises(TypeError):
        make_from_obj(instance, 'name', instance.name)


def test_load_error(bound_session):
    instance = Model(name='name')
    bound_session.add(instance)
    with pytest.raises(TypeError):
        load(instance, None)


# nullable translatable fields

def test_required_field_missing(bound_session):
    model = RequiredModel()
    bound_session.add(model)
    with pytest.raises(OperationalError):
        bound_session.commit()


def test_required_field(bound_session):
    model = RequiredModel(name="bar")
    bound_session.add(model)
    bound_session.commit()
