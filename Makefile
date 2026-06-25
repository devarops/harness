all: check coverage mutants

.PHONY: \
		all \
		check \
		clean \
		coverage \
		format \
		init \
		install \
		linter \
		mutants \
		setup \
		tests

module = harness

define lint
	pylint \
        --disable=bad-continuation \
        --disable=missing-class-docstring \
        --disable=missing-function-docstring \
        --disable=missing-module-docstring \
        ${1}
endef

check:
	black --check --line-length 100 ${module}
	black --check --line-length 100 tests
	flake8 --max-line-length 100 ${module}
	flake8 --max-line-length 100 tests
	mypy ${module}
	mypy tests

clean:
	rm --force --recursive .*_cache
	rm --force --recursive *.egg-info
	rm --force --recursive ${module}/__pycache__
	rm --force --recursive tests/__pycache__
	rm --force .mutmut-cache
	rm --force coverage.xml

coverage: setup
	pytest --cov=${module} --cov-report=xml --verbose && \
	coverage report --show-missing

format:
	black --line-length 100 ${module}
	black --line-length 100 tests

init: init_git setup tests

init_git:
	git config --global --add safe.directory /workdir
	git config --global user.name "Evaristo Rojas"
	git config --global user.email "evaristo.rojas@islas.org.mx"

install:
	pip install --editable .

linter:
	$(call lint, ${module})
	$(call lint, tests)

mutants: setup
	mutmut run --paths-to-mutate ${module}

setup: clean install

tests: tests_python

tests_python:
	pytest --verbose
