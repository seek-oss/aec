MAKEFLAGS += --warn-undefined-variables
SHELL = /bin/bash -o pipefail
.DEFAULT_GOAL := help
.PHONY: help install test lint black autopep8 install-config 

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

$(venv): requirements.txt requirements.dev.txt $(pip)
	$(pip) install -e '.[dev]'
	touch $(venv)

## create venv and install this package in editable mode
install: $(venv)

## run tests
test: $(venv)
	$(venv)/bin/pytest

## lint code
lint: $(venv)
	$(venv)/bin/pylint $(src)

## format code using black
black: $(venv)
	$(venv)/bin/black $(src)
	$(venv)/bin/isort --recursive --multi-line=3 --trailing-comma --apply $(src)

## format code using autopep8
autopep8: $(venv)
	$(venv)/bin/autopep8 --in-place -r $(src)
	$(venv)/bin/isort --recursive --multi-line=3 --trailing-comma --apply $(src)

## install example config files in ~/.aec/ (if they don't already exist)
install-config:
	@mkdir -p ~/.aec/
	@cp -r conf/* ~/.aec/
	@(cp -rn ~/.aec/ec2.example.toml ~/.aec/ec2.toml && echo "Installed config into ~/.aec/") || echo "Didn't overwrite existing files"