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
