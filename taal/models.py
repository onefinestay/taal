from __future__ import absolute_import

from sqlalchemy import Column, String, Text


class TranslationMixin(object):
    context = Column(String(255, collation='utf8_bin'), primary_key=True)
    message_id = Column(String(255, collation='utf8_bin'), primary_key=True)
    language = Column(String(255, collation='utf8_bin'), primary_key=True)
    value = Column(Text())
