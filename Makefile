ifdef TRAVIS
	MYSQL := --db_uri="mysql://travis@127.0.0.1/test_db?charset=utf8&use_unicode=0"
	NEO4J := --neo4j_uri=http://localhost:7474/db/data/
endif


noop:
	@true

.PHONY: noop

develop:
	python setup.py develop
	pip install -r test_requirements.txt

pytest:
	py.test --cov taal --cov-report term-missing tests ${MYSQL} ${NEO4J}

flake8:
	flake8 taal tests

test: flake8 pytest

docs/api/modules.rst: $(wildcard taal/**/*.py)
	sphinx-apidoc -f -o docs/api taal

autodoc: docs/api/modules.rst

docs: autodoc
	cd docs && make html
