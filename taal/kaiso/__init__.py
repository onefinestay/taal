from __future__ import absolute_import

from kaiso.attributes import String

from taal import is_translatable_value
from taal.constants import PLACEHOLDER, TRANSPARENT_VALUES, PlaceholderValue


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

            # can't prevent this from being returned to the user
            # in the case of a direct query for Model.field
            # Return something that's more likely to error early
            # than a string
            return PlaceholderValue

        raise RuntimeError(
            "Unexpected value found in placeholder column: '{}'".format(value))
