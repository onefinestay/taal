import pytest

from tests.helpers import get_translator
from tests.models import ConcreteTranslation, Parent, Child, CustomFields


def test_refresh_with_relationship(session):
    """ regression: refreshing attribute that isn't a column name """

    with get_translator(ConcreteTranslation, 'en') as translator:
        translator.bind(session)
        parent = Parent()
        child = Child(parent=parent)
        session.add(child)
        session.commit()

        assert parent.children == [child]


def test_merge_from_other_session(session):
    """ regression test """

    with get_translator(ConcreteTranslation, 'en') as translator:
        translator.bind(session)
        instance = CustomFields()
        session.merge(instance)


def test_assign_between_models(session):
    """ regression: ModelA().translated_field = modelB().translated_field """

    model_a = CustomFields(id=1, name="name")
    with pytest.raises(NotImplementedError):
        Child(id=2, name=model_a.name)

    # model_b = Child(id=2, name=model_a.name)

    # with get_translator(ConcreteTranslation, 'en') as translator:
        # translator.bind(session)
        # session.add(model_a)
        # session.add(model_b)
        # session.commit()

        # assert translator.translate(model_b.name) == 'name'
