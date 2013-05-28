from __future__ import absolute_import

import json

import sqlalchemy.types as types
from sqlalchemy.orm import class_mapper

from taal import TranslatableString as TaalTranslatableString


def get_context(table, column):
    return "taal:sa_field:{}:{}".format(table, column)


def get_message_id(obj):
    cls = obj.__class__
    mapper = class_mapper(cls)
    primary_keys = mapper.primary_key_from_instance(obj)
    return json.dumps(primary_keys)


class TranslatableString(types.TypeDecorator):

    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is not None:
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Value was {}".format(value))

    def process_result_value(self, value, dialect):
        return TaalTranslatableString(None, None)
