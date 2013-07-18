ifdef TRAVIS
	MYSQL := --db_uri=mysql://travis@127.0.0.1/test_db
	NEO4J := --neo4j_uri=http://localhost:7474/db/data/
endif


noop:
	@true

.PHONY: noop

develop:
	python setup.py develop
	pip install -r test_requirements.txt

pytest:
	py.test --cov taal tests ${MYSQL} ${NEO4J}

flake8:
	flake8 taal tests

test: pytest flake8

docs/api/modules.rst: $(wildcard taal/**/*.py)
	sphinx-apidoc -f -o docs/api taal

autodoc: docs/api/modules.rst

docs: autodoc
	cd docs && make html
