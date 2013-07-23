from __future__ import absolute_import

from sqlalchemy import Column, String, Text


class TranslationMixin(object):
    """ Mixin for sqlalchemy model to contain translation data

        Usage:
            Base = declarative_base()

            class MyTranslations(TranslationMixin, Base):
                __tablename__ = "my_translations"
    """

    context = Column(String(255, collation='utf8_bin'), primary_key=True)
    message_id = Column(String(255, collation='utf8_bin'), primary_key=True)
    language = Column(String(255, collation='utf8_bin'), primary_key=True)
    value = Column(Text(convert_unicode=True))
