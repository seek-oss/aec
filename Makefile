MAKEFLAGS += --warn-undefined-variables
SHELL = /bin/bash -o pipefail
.DEFAULT_GOAL := help
.PHONY: help venv test install

venv = ~/.virtualenvs/asak
python := $(venv)/bin/python
pip := $(venv)/bin/pip

$(venv): requirements.txt requirements.dev.txt
	$(if $(value VIRTUAL_ENV),$(error Cannot create a virtualenv when running in a virtualenv. Please deactivate the current virtual env $(VIRTUAL_ENV)),)
	python3 -m venv --clear $(venv) && $(venv)/bin/pip install -r requirements.txt && $(venv)/bin/pip install -r requirements.dev.txt

## set up python virtual env (named asak) and install requirements
venv: $(venv)

## display this help message
help:
	@awk '/^##.*$$/,/^[~\/\.a-zA-Z_-]+:/' $(MAKEFILE_LIST) | awk '!(NR%2){print $$0p}{p=$$0}' | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

## run tests
test: $(venv)
	$(venv)/bin/pytest

## install example config files (if they don't already exist)
install-example-config:
	mkdir -p ~/.asak/
	cp -r conf/* ~/.asak/
	cp -rn ~/.asak/ec2.example.toml ~/.asak/ec2.toml || true

## install the tools
install: $(venv)
	$(pip) install -e .

