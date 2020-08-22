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
	# create empty virtualenv containing pip
	$(if $(value VIRTUAL_ENV),$(error Cannot create a virtualenv when running in a virtualenv. Please deactivate the current virtual env $(VIRTUAL_ENV)),)
	python3 -m venv --clear $(venv)

$(venv): requirements.* setup.py $(pip)
	$(pip) install -e '.[dev]'
	$(venv)/bin/nodeenv -p -n system -r requirements.node.dev.txt

	rm -rf typings/

	# workaround for https://github.com/vemel/mypy_boto3_builder/issues/39
	mkdir -p typings/boto3
	cp $(venv)/lib/python*/site-packages/mypy_boto3/boto3_init_gen.py typings/boto3/__init__.pyi

	# needed for pyright to detect type errors on boto client/resources, and also autocomplete in vscode
	# NB: type_defs is not included because it takes 20 sec for pyright to parse!
	mkdir -p typings/mypy_boto3_ec2
	for f in __init__ client paginater service_resource waiter; do \
		cp $(venv)/lib/python*/site-packages/mypy_boto3_ec2/$$f.py typings/mypy_boto3_ec2/$$f.pyi; done

	touch $(venv)

## create venv, install this package in dev mode, and install hooks (if not in CI)
install: $(venv) $(if $(value CI),,install-hooks)

## lint code and run static type check
check: lint pyright

## lint
lint: install-hooks
	$(venv)/bin/pre-commit run --all-files --hook-stage push flake8

## pyright
pyright: $(venv)
	source $(venv)/bin/activate && pyright

## run tests
test: $(venv)
	$(venv)/bin/pytest

## run pre-commit git hooks on all files
hooks: install-hooks
	$(venv)/bin/pre-commit run --all-files --hook-stage push

install-hooks: .git/hooks/pre-commit .git/hooks/pre-push

.git/hooks/pre-commit: $(venv)
	$(venv)/bin/pre-commit install -t pre-commit

.git/hooks/pre-push: $(venv)
	$(venv)/bin/pre-commit install -t pre-push

## build source dist
dist: $(src) setup.py MANIFEST.in
	rm -rf aec.egg-info
	rm -rf dist
	python setup.py sdist
