from __future__ import absolute_import

from kaiso.attributes import String

from taal.constants import PLACEHOLDER


def is_translatable_value(value):
    return value not in ("", None)


class TranslatableString(String):
    @staticmethod
    def to_primitive(value, for_db):
        if for_db and value not in (None, "", PLACEHOLDER):
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Value was '{}'".format(value))

        return value
