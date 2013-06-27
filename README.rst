Taal
====


Develop
-------

To make your life easier, create a ``setup.cfg`` file with a ``[pytest]``
section to define your database and neo4j connection strings::

    $ cat setup.cfg
    [pytest]
    addopts= --neo4j_uri=http://... --db_uri=mysql://...
