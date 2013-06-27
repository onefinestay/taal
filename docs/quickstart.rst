Quickstart
==========


SQLAlchemy
----------

Create your models, using the column type ``TranslatableString``::

    from sqlalchemy import Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base

    from taal import Translator
    from taal.sqlalchemy import TranslatableString, events


    Base = declarative_base()


    class Translation(TranslationMixin, Base):
        __tablename__ = "test_translations"


    class MyModel(Base):
        __tablename__ = "my_model"

        id = Column(Integer, primary_key=True)
        identifier = Column(String(20))
        name = Column(TranslatableString())  # will be translated


Attributes are automatically (and immediately) converted to placeholders::

    >>> instance = MyModel(id=1)
    >>> instance.name
    <TranslatableString: (taal:sa_field:my_model:name, [1], None)>


Register your session to have translations automatically persisted::

    >>> translator_session = Session()  # for use by the translator
    >>> session = Sesssion()
    >>> translator = Translator(Translation, translator_session, 'en')
    translator.bind(session)  # register your session for translations

    >>> instance.name = "Spam"
    >>> session.add(instance)
    >>> session.commit()

    # the translated value is automatiaclly inserted into the translations
    # table, along with some contextual information
    >>> translation = session.query(Translation).first()
    >>> translation.context, translation.message_id, translation.language,
    ... translation.value
    ('taal:sa_field:my_model:name', '[1]', 'en', 'Spam')

    >>> instance.name
    <TranslatableString: (taal:sa_field:my_model:name, [1], None)>

    >>> translator.translate(instance.name)
    'Spam'


You can also translate a ``TranslatableString`` inside a python data structure::

    >>> translator.translate({'key': ['list', instance.name]})
    {'key': ['list', 'Spam']}

