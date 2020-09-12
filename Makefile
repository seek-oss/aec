MAKEFLAGS += --warn-undefined-variables
SHELL = /bin/bash -o pipefail
.DEFAULT_GOAL := help
.PHONY: help install check flake8 pyright test hooks install-hooks

## display help message
help:
	@awk '/^##.*$$/,/^[~\/\.0-9a-zA-Z_-]+:/' $(MAKEFILE_LIST) | awk '!(NR%2){print $$0p}{p=$$0}' | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

venv = venv
pip := $(venv)/bin/pip
src := aec tests

$(pip):
	# create empty virtualenv containing pip
	$(if $(value VIRTUAL_ENV),$(error Cannot create a virtualenv when running in a virtualenv. Please deactivate the current virtual env $(VIRTUAL_ENV)),)
	python3 -m venv --clear $(venv)
	$(pip) install wheel

$(venv): setup.py $(pip)
	$(pip) install -e '.[dev]'
	touch $(venv)

# install pyright stubs
typings: $(venv)
	rm -rf typings/
	VIRTUAL_ENV=$(venv) ./.install-typings-boto3.sh
	touch typings

## create venv, install this package in dev mode, create stubs, and install hooks (if not in CI)
install: $(venv) node_modules typings $(if $(value CI),,install-hooks)

## lint code and run static type check
check: flake8 pyright

## lint using flake8
flake8: $(venv)
	$(venv)/bin/flake8

node_modules: package.json
	npm install
	touch node_modules

## pyright
pyright: node_modules typings $(venv)
	source $(venv)/bin/activate && node_modules/.bin/pyright

## run tests
test: $(venv)
	$(venv)/bin/pytest

## run pre-commit git hooks on all files
hooks: install-hooks $(venv)
	$(venv)/bin/pre-commit run --all-files --hook-stage push

install-hooks: .git/hooks/pre-commit .git/hooks/pre-push

.git/hooks/pre-commit: $(venv)
	$(venv)/bin/pre-commit install -t pre-commit

.git/hooks/pre-push: $(venv)
	$(venv)/bin/pre-commit install -t pre-push

## build source dist
dist: $(src) setup.py MANIFEST.in
	# remove previous build remnants
	rm -rf *.egg-info
	$(venv)/bin/python setup.py sdist

## test the distribution is correctly packaged
test-dist: $(venv)
	# remove previous build remnants (tox builds in . so sees this too)
	rm -rf *.egg-info

	# recreate distribution package (sdist) and run aec help
	$(venv)/bin/tox -v -r -e py

test-dist-no-tox: $(venv) dist
	$(venv)/bin/python3 -m venv --clear /tmp/aec-test-dist
	/tmp/aec-test-dist/bin/pip install dist/*.tar.gz
	/tmp/aec-test-dist/bin/aec ec2 -h
