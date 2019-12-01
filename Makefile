MAKEFLAGS += --warn-undefined-variables
SHELL = /bin/bash -o pipefail
.DEFAULT_GOAL := help
.PHONY: help venv test install install-example-config

venv = ~/.virtualenvs/aec
python := $(venv)/bin/python
pip := $(venv)/bin/pip

$(venv): requirements.txt requirements.dev.txt
	$(if $(value VIRTUAL_ENV),$(error Cannot create a virtualenv when running in a virtualenv. Please deactivate the current virtual env $(VIRTUAL_ENV)),)
	python3 -m venv --clear $(venv) && $(pip) install -r requirements.txt && $(pip) install -r requirements.dev.txt

## set up python virtualenv (named aec) and install requirements
venv: $(venv)

## display this help message
help:
	@awk '/^##.*$$/,/^[~\/\.a-zA-Z_-]+:/' $(MAKEFILE_LIST) | awk '!(NR%2){print $$0p}{p=$$0}' | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

## run tests
test: $(venv)
	$(venv)/bin/pytest

## install example config files (if they don't already exist)
install-example-config:
	@mkdir -p ~/.aec/
	@cp -r conf/* ~/.aec/
	@(cp -rn ~/.aec/ec2.example.toml ~/.aec/ec2.toml && echo "Installed config into ~/.aec/") || echo "Didn't overwrite existing files"

## install aec from this local clone (useful during development)
install: $(venv)
	$(pip) install -e .

## lint code
lint: $(venv)
	$(venv)/bin/pylint tests tools

