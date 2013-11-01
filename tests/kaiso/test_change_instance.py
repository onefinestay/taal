from __future__ import absolute_import

from kaiso.attributes import Integer
from kaiso.types import Entity
import pytest

from taal import Translator
from taal import kaiso as taal_kaiso

from tests.models import Translation


@pytest.fixture
def change_instance_hierarchy(bound_manager):
    manager = bound_manager

    class Common(Entity):
        id = Integer(unique=True)
        common = taal_kaiso.TranslatableString()

    class Old(Common):
        old = taal_kaiso.TranslatableString()

    class New(Common):
        new = taal_kaiso.TranslatableString()

    manager.save(Old)
    manager.save(New)
    obj = Old(id=1, common="common", old="old")
    manager.save(obj)
    return obj


def test_change_instance_type(
        bound_manager, session, change_instance_hierarchy):
    manager = bound_manager
    obj = change_instance_hierarchy

    assert session.query(Translation).count() == 2

    retrieved = manager.deserialize(manager.serialize(obj))
    new = manager.change_instance_type(retrieved, 'New')

    # make sure we reset our session
    session.rollback()

    data = manager.serialize(new)
    translator = Translator(Translation, session, 'language')
    translated = translator.translate(data)

    assert translated['common'] == 'common'
    assert session.query(Translation).count() == 1


def test_updated_values(
        session, bound_manager, change_instance_hierarchy):
    manager = bound_manager
    obj = change_instance_hierarchy

    retrieved = manager.deserialize(manager.serialize(obj))
    new = manager.change_instance_type(retrieved, 'New', {'new': 'new'})

    data = manager.serialize(new)
    translator = Translator(Translation, session, 'language')
    translated = translator.translate(data)

    assert translated['common'] == 'common'
    assert translated['new'] == 'new'
    assert session.query(Translation).count() == 2


def test_update_existing_values(
        session, bound_manager, change_instance_hierarchy):
    manager = bound_manager
    obj = change_instance_hierarchy

    retrieved = manager.deserialize(manager.serialize(obj))
    new = manager.change_instance_type(retrieved, 'New', {'common': 'new'})

    data = manager.serialize(new)
    translator = Translator(Translation, session, 'language')
    translated = translator.translate(data)

    assert translated['common'] == 'new'
    assert session.query(Translation).count() == 1


def test_update_removed_values(
        session, bound_manager, change_instance_hierarchy):
    manager = bound_manager
    obj = change_instance_hierarchy

    retrieved = manager.deserialize(manager.serialize(obj))
    new = manager.change_instance_type(retrieved, 'New', {'old': 'new'})

    data = manager.serialize(new)
    translator = Translator(Translation, session, 'language')
    translated = translator.translate(data)

    assert translated['common'] == 'common'
    assert session.query(Translation).count() == 1


def test_update_unknown_values(
        session, bound_manager, change_instance_hierarchy):
    manager = bound_manager
    obj = change_instance_hierarchy

    retrieved = manager.deserialize(manager.serialize(obj))
    new = manager.change_instance_type(retrieved, 'New', {'unknown': 'new'})

    data = manager.serialize(new)
    translator = Translator(Translation, session, 'language')
    translated = translator.translate(data)

    assert translated['common'] == 'common'
    assert session.query(Translation).count() == 1
