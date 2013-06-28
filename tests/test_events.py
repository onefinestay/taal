from taal import Translator
from tests.models import ConcreteTranslation, Parent, Child, CustomFields


def test_refresh_with_relationship(session, session_cls):
    """ regression: refreshing attribute that isn't a column name """

    translator = Translator(ConcreteTranslation, session_cls(), 'en')
    translator.bind(session)
    parent = Parent()
    child = Child(parent=parent)
    session.add(child)
    session.commit()

    assert parent.children == [child]


def test_merge_from_other_session(session, session_cls):
    """ regression test """

    translator = Translator(ConcreteTranslation, session_cls(), 'en')
    translator.bind(session)
    instance = CustomFields()
    session.merge(instance)
