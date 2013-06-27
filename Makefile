noop:
	@true

.PHONY: noop

develop:
	python setup.py develop
	pip install -r test_requirements.txt

pytest:
	py.test --cov taal tests

flake8:
	flake8

test: pytest flake8

docs/api/modules.rst: $(wildcard taal/**/*.py)
	sphinx-apidoc -f -o docs/api taal

autodoc: docs/api/modules.rst

docs: autodoc
	cd docs && make html
