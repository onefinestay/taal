from __future__ import absolute_import

from kaiso.attributes import String


class TranslatableString(String):
    @staticmethod
    def to_primitive(value, for_db):
        if not for_db:
            return value

        if value is not None:
            raise RuntimeError(
                "Cannot save directly to translated fields. "
                "Value was '{}'".format(value))
