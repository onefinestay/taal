from __future__ import absolute_import

from sqlalchemy import Column, String, Text


class TranslationMixin(object):
    context = Column(String(255), primary_key=True)
    message_id = Column(String(255), primary_key=True)
    language = Column(String(255), primary_key=True)
    translation = Column(Text())
