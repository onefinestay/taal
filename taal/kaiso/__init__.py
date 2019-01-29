from __future__ import absolute_import

from kaiso.attributes import String

from taal.constants import PLACEHOLDER, TRANSPARENT_VALUES, PlaceholderValue
from taal.translatablestring import is_translatable_value

TYPE_CONTEXT = "taal:kaiso_type"


class TranslatableString(String):
    @staticmethod
    def to_primitive(value, for_db):
        acceptable_values = TRANSPARENT_VALUES + (PLACEHOLDER,)

        if for_db and value not in acceptable_values:
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Value was '{}'".format(value))

        return value

    @staticmethod
    def to_python(value):

        if not is_translatable_value(value):
            return value

        if value == PLACEHOLDER:
            # Before translation, return a placeholder that's more likely to
            # generate an error than a normal string.
            return PlaceholderValue

        raise RuntimeError(
            "Unexpected value found in placeholder column: '{}'".format(value))
