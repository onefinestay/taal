from __future__ import absolute_import

import pytest
from sqlalchemy.exc import StatementError

from taal import Translator, TranslatableString
from taal.sqlalchemy.events import flush_log
from taal.sqlalchemy.types import get_context, get_message_id

from tests.models import (
    CustomFields, ConcreteTranslation, create_translation_for_model)

from tests.helpers import get_session, get_translator


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


def test_delete(session):
    model = CustomFields()
    session.add(model)
    session.commit()

    create_translation_for_model(
        session, 'english', model, 'name', 'English name')

    context = get_context(CustomFields, 'name')
    message_id = get_message_id(model)
    translatable = TranslatableString(context=context, message_id=message_id)

    translator = Translator(
        ConcreteTranslation, session, 'english', debug_output=True)
    translator.delete_translation(translatable)

    translation = translator.translate(translatable)
    assert "[Translation missing" in translation


def test_save_empty(session):
    translatable = TranslatableString()
    translator = Translator(ConcreteTranslation, session, 'english')
    with pytest.raises(RuntimeError):
        translator.save_translation(translatable)


class TestMagic(object):
    def test_init(self):
        instance = CustomFields(name='name')
        assert isinstance(instance.name, TranslatableString)
        assert not isinstance(instance.name.value, TranslatableString)

    def test_set(self):
        instance = CustomFields()
        instance.name = 'name'
        assert isinstance(instance.name, TranslatableString)
        assert not isinstance(instance.name.value, TranslatableString)

    def test_set_none(self):
        instance = CustomFields()
        instance.name = None
        assert instance.name is None

    def test_set_from_other(self):
        first = CustomFields(name='name')
        second = CustomFields()
        second.name = first.name
        assert isinstance(second.name, TranslatableString)
        assert not isinstance(second.name.value, TranslatableString)

    def test_init_from_other(self):
        first = CustomFields(name='name')
        second = CustomFields(name=first.name)
        assert isinstance(second.name, TranslatableString)
        assert not isinstance(second.name.value, TranslatableString)

    def test_init_from_none(self):
        instance = CustomFields()
        assert instance.name is None

    def test_change_from_init(self):
        instance = CustomFields(name='a')
        instance.name = 'b'
        assert isinstance(instance.name, TranslatableString)
        assert instance.name.value == 'b'

    def test_refresh(self, session):
        instance = CustomFields()
        session.add(instance)
        session.commit()

        loaded = session.query(CustomFields).get(instance.id)
        assert isinstance(loaded.name, TranslatableString)
        assert not isinstance(loaded.name.value, TranslatableString)

    def test_refresh_with_value(self, session):
        instance = CustomFields(name='name')

        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            session.add(instance)
            session.commit()

            loaded = session.query(CustomFields).get(instance.id)
            assert isinstance(loaded.name, TranslatableString)
            translation = session.query(ConcreteTranslation).one()
            assert translation.value == 'name'

    def test_query(self, session):
        instance = CustomFields(name='name')

        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            session.add(instance)
            session.commit()

            loaded = session.query(CustomFields).filter(
                CustomFields.id == instance.id).one()
            assert isinstance(loaded.name, TranslatableString)
            session.close()
            translation = session.query(ConcreteTranslation).one()
            assert translation.value == 'name'

    def test_modify(self, session):
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            instance = CustomFields(name='a')
            session.add(instance)
            session.commit()

            with get_session() as translator_session:
                assert translator_session.query(ConcreteTranslation).value(
                    ConcreteTranslation.value) == 'a'

            instance.name = 'b'
            session.commit()

            with get_session() as translator_session:
                assert translator_session.query(ConcreteTranslation).value(
                    ConcreteTranslation.value) == 'b'

    def test_load(self, session):
        instance = CustomFields()
        session.add(instance)
        session.commit()

        with get_session() as new_session:
            loaded = new_session.query(CustomFields).get(instance.id)
        assert isinstance(loaded.name, TranslatableString)
        assert not isinstance(loaded.name.value, TranslatableString)

    def test_save(self, session):
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            instance = CustomFields(name='name')
            session.add(instance)
            session.commit()

        assert session.query(ConcreteTranslation).value(
            ConcreteTranslation.value) == 'name'

    def test_save_none(self, session):
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            instance = CustomFields()
            session.add(instance)
            session.commit()

        assert session.query(ConcreteTranslation).value(
            ConcreteTranslation.value) is None

    def test_change_language(self, session):
        session.add(ConcreteTranslation(
            context=get_context(CustomFields(), 'name'),
            message_id="[1]",
            language="en",
            value="en name"
        ))
        session.add(ConcreteTranslation(
            context=get_context(CustomFields(), 'name'),
            message_id="[1]",
            language="fr",
            value="fr name"
        ))

        with get_translator(ConcreteTranslation, 'en') as translator:
            with get_translator(ConcreteTranslation, 'fr') as translator_fr:
                translator.bind(session)

                instance_en = CustomFields(name='new en name')
                session.add(instance_en)
                session.commit()
                id_ = instance_en.id

                instance_fr = session.query(CustomFields).get(id_)
                assert translator_fr.translate(instance_fr.name) == 'fr name'

                values = session.query(ConcreteTranslation).values(
                    ConcreteTranslation.language, ConcreteTranslation.value)
                assert set(values) == set([
                    ('en', 'new en name'),
                    ('fr', 'fr name'),
                ])

    def test_update(self, session):
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            instance = CustomFields(name='name')
            session.add(instance)
            session.commit()

            with pytest.raises(StatementError):
                session.query(CustomFields).update({'name': 'updated_name'})

    def test_flushing(self, session):
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            instance = CustomFields(name='name')
            session.add(instance)

            assert instance.name is not None
            session.flush()
            assert instance.name is not None

    def test_deleting(self, session):
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            instance = CustomFields(name='name')
            session.add(instance)
            session.commit()

            assert session.query(ConcreteTranslation).count() == 1

            session.delete(instance)
            assert session.query(ConcreteTranslation).count() == 1

            session.commit()
            assert session.query(ConcreteTranslation).count() == 0

    def test_rollback(self):
        """ TODO """

    def test_bulk_update(self):
        """ TODO (?) """


class TestSavepoints(object):
    def test_verify(self, session):
        # check the test setup works
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            assert session not in flush_log
            assert translator.session not in flush_log

            instance1 = CustomFields(name='instance 1')
            session.add(instance1)

            session.flush()
            assert session in flush_log
            assert len(flush_log[session]) == 1
            session.commit()
            assert session not in flush_log

            instance2 = CustomFields(name='instance 2')
            session.add(instance2)
            session.commit()
            assert session not in flush_log
            assert session.query(ConcreteTranslation).count() == 2

    def test_savepoints(self, session):
        with get_translator(ConcreteTranslation, 'en') as translator:
            translator.bind(session)

            instance1 = CustomFields(name='instance 1')
            session.add(instance1)

            session.begin_nested()

            instance2 = CustomFields(name='instance 2')
            session.add(instance2)
            session.flush()
            assert session in flush_log
            assert len(flush_log[session]) == 2

            session.rollback()
            session.commit()

            assert session.query(CustomFields).count() == 1
            assert session.query(ConcreteTranslation).count() == 1
