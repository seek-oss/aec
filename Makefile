MAKEFLAGS += --warn-undefined-variables
SHELL = /bin/bash -o pipefail
.DEFAULT_GOAL := help
.PHONY: help install-config install test lint black autopep8

venv = ~/.virtualenvs/aec
python := $(venv)/bin/python
pip := $(venv)/bin/pip

$(pip):
	# create new virtualenv $(venv) containing pip
	$(if $(value VIRTUAL_ENV),$(error Cannot create a virtualenv when running in a virtualenv. Please deactivate the current virtual env $(VIRTUAL_ENV)),)
	python3 -m venv --clear $(venv)

$(venv): requirements.txt requirements.dev.txt $(pip)
	$(pip) install -e '.[dev]'
	touch $(venv)

## display this help message
help:
	@awk '/^##.*$$/,/^[~\/\.a-zA-Z_-]+:/' $(MAKEFILE_LIST) | awk '!(NR%2){print $$0p}{p=$$0}' | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

## install example config files in ~/.aec/ (if they don't already exist)
install-config:
	@mkdir -p ~/.aec/
	@cp -r conf/* ~/.aec/
	@(cp -rn ~/.aec/ec2.example.toml ~/.aec/ec2.toml && echo "Installed config into ~/.aec/") || echo "Didn't overwrite existing files"

## install aec in editable mode (useful during development)
install: $(venv)

## run tests
test: $(venv)
	$(venv)/bin/pytest

## lint code
lint: $(venv)
	$(venv)/bin/pylint tests tools

## format code using black
black: $(venv)
	$(venv)/bin/black tests tools
	$(venv)/bin/isort --recursive --multi-line=3 --trailing-comma --apply tests tools

## format code using autopep8
autopep8: $(venv)
	$(venv)/bin/autopep8 --in-place -r tests tools
	$(venv)/bin/isort --recursive --multi-line=3 --trailing-comma --apply tests tools