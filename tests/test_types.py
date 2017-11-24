from __future__ import absolute_import

from taal.translatablestring import TranslatableString


class TestComparison(object):
    def test_empty(self):
        s1 = TranslatableString()
        s2 = TranslatableString()

        assert s1 == s2

    def test_equal(self):
        s1 = TranslatableString(context='c', message_id='m')
        s2 = TranslatableString(context='c', message_id='m')

        assert s1 == s2

    def test_not_equal(self):
        s1 = TranslatableString(context='c', message_id='m')
        s2 = TranslatableString(context='c', message_id='mmm')

        assert s1 != s2
