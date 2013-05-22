from sqlalchemy.ext.declarative import declarative_base

from taal.models import TranslationMixin


Base = declarative_base()


class ConcreteTranslation(TranslationMixin, Base):
    __tablename__ = "test_translations"


