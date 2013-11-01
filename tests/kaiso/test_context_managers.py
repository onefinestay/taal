from __future__ import absolute_import

from taal import translation_manager
from taal.kaiso.context_managers import (
    TypeTranslationContextManager, AttributeTranslationContextManager)


def test_kaiso_context_managers(manager, type_heirarchy):
    type_context_manager = TypeTranslationContextManager(manager)
    message_ids = set(type_context_manager.list_message_ids())
    assert message_ids == set(['Entity', 'Animal', 'Fish'])

    attr_context_manager = AttributeTranslationContextManager(manager)
    message_ids = set(attr_context_manager.list_message_ids())
    assert message_ids == set(['["Animal", "id"]', '["Animal", "name"]'])


def test_kaiso_translation_manager(manager, type_heirarchy):
    context_message_id_pairs = set(
        translation_manager.list_contexts_and_message_ids(
            manager=manager))
    assert context_message_id_pairs == set([
        ('taal:kaiso_type', 'Entity'),
        ('taal:kaiso_type', 'Animal'),
        ('taal:kaiso_type', 'Fish'),
        ('taal:kaiso_attr', '["Animal", "id"]'),
        ('taal:kaiso_attr', '["Animal", "name"]'),
    ])
