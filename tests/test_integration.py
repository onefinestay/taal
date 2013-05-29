from __future__ import absolute_import

import pytest

from taal import Translator
from taal.kaiso import TypeTranslationContextManager, get_type_hierarchy

from tests.kaiso import Fish
from tests.models import ConcreteTranslation


def serialize_type_hierarchy(storage):
    """
    Get a flattened type hierarchy.
    """

    types = {}
    for type_id, label, bases, attrs in get_type_hierarchy(storage):

        attr_dict = {}
        for attr in attrs:
            attr_dict[attr.name] = storage.serialize(attr)

        # include inherited attributes
        for base in bases:
            for inherited_attr_name, inherited_attr in (
                    types[base]['attributes'].items()):
                # ignoring those that have been redeclared
                if inherited_attr_name not in attr_dict:
                    attr_dict[inherited_attr_name] = inherited_attr

        types[type_id] = {
            'label': label,
            'bases': bases,
            'attributes': attr_dict
        }
    return types


class TestKaiso(object):
    # Couldn't figure out how to inject fixtures into setup_method
    def _setup_kaiso(self, storage):
        storage.save(Fish)

    def _setup_db(self, session):
        context = TypeTranslationContextManager.context
        translation = ConcreteTranslation(
            context=context,
            message_id='Fish',
            translation='Translated Fish',
            language='language'
        )
        session.add(translation)
        session.commit()

    @pytest.mark.usefixtures('storage')
    @pytest.mark.usefixtures('session')
    def test_kaiso_patching(self, session, storage):
        self._setup_db(session)
        self._setup_kaiso(storage)
        serialized_hierarchy = serialize_type_hierarchy(storage)

        fish = serialized_hierarchy['Fish']
        translator = Translator(ConcreteTranslation, session, 'language')
        translated_fish = translator.translate(fish)

        assert translated_fish['label'] == 'Translated Fish'
