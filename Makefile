MAKEFLAGS += --warn-undefined-variables
SHELL = /bin/bash -o pipefail
.DEFAULT_GOAL := help
.PHONY: help install test lint check hooks install-hooks

## display help message
help:
	@awk '/^##.*$$/,/^[~\/\.0-9a-zA-Z_-]+:/' $(MAKEFILE_LIST) | awk '!(NR%2){print $$0p}{p=$$0}' | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

venv = ~/.virtualenvs/aec
pip := $(venv)/bin/pip
src := tools tests

$(pip):
	# create empty virtualenv with basics like pip
	$(if $(value VIRTUAL_ENV),$(error Cannot create a virtualenv when running in a virtualenv. Please deactivate the current virtual env $(VIRTUAL_ENV)),)
	python3 -m venv --clear $(venv)

$(venv): requirements.txt requirements.dev.txt setup.py $(pip)
	$(pip) install -e '.[dev]'
	touch $(venv)

## create venv, install this package in dev mode, and install hooks (if not in CI)
install: $(venv) $(if $(value CI),,install-hooks)

## lint
lint:
	pre-commit run --all-files --hook-stage push flake8

## check
check:
	pre-commit run --all-files --hook-stage push pyright

## run tests
test: $(venv)
	$(venv)/bin/pytest

## run pre-commit hooks on all files
hooks: install-hooks
	pre-commit run --all-files --hook-stage push

install-hooks: .git/hooks/pre-commit .git/hooks/pre-push

.git/hooks/pre-commit: 
	pre-commit install -t pre-commit

.git/hooks/pre-push:
	pre-commit install -t pre-push

## build source dist
dist: $(src) setup.py MANIFEST.in
	rm -rf aec.egg-info
	rm -rf dist
	python setup.py sdist
