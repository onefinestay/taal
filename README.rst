Taal
====

Taal is a framework for translating your data. It plugs in to e.g. `SQLAlchemy
<http://www.sqlalchemy.org/>`_ or `Kaiso
<https://github.com/onefinestay/kaiso/>`_, providing a ``TranslatableString``
field type and a mechanism for storing and retrieving content in multiple
languages.


For use-cases where the most common interaction with the translated data is for
reading, an application can be set up so that language context and translations
are handled centrally, after which business logic can be written almost as it
would for a single-language app.

Philosophy
----------

Taal uses a two-phase process for managing translatable data. Upon retrieval,
data is marked up as "requires translation". Subsequently (typically higher up
in the stack, e.g. in some middleware), information about which particular
language we are interested in may be supplied to find the actual translation
string.


Example use
-----------

::

    class MyModel(Base):
        __tablename__ = "my_model"

        id = Column(Integer, primary_key=True)
        name = Column(TranslatableString())

::


    >>> instance = session.query(MyModel).first()
    >>> instance.name
    <TranslatableString: (...)>

    >>> translator = get_translator('en')
    >>> translator.translate(instance.name)
    "Spam"


Development
===========

To make your life easier, create a ``setup.cfg`` file with a ``[pytest]``
section to define your database and neo4j connection strings::

    $ cat setup.cfg
    [pytest]
    addopts= --neo4j_uri=http://... --db_uri=mysql://...

(Note that pytest gets upset if you indent the ``addopts`` line)
