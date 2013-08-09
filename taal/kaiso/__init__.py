from __future__ import absolute_import

from kaiso.attributes import String

from taal.constants import PLACEHOLDER, TRANSPARENT_VALUES


class TranslatableString(String):
    @staticmethod
    def to_primitive(value, for_db):
        acceptable_values = TRANSPARENT_VALUES + (PLACEHOLDER,)

        if for_db and value not in acceptable_values:
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Value was '{}'".format(value))

        return value
