from tests.helpers import get_translator
from tests.models import ConcreteTranslation, Parent, Child


def test_refresh_with_relationship(session):
    """ regression: refreshing attribute that isn't a column name """

    with get_translator(ConcreteTranslation, 'en') as translator:
        translator.bind(session)
        parent = Parent()
        child = Child(parent=parent)
        session.add(child)
        session.commit()

        assert parent.children == [child]
