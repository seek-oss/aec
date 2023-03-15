# Contributing 🌳

## Prerequisites

- make
- node (required for pyright)
- python >= 3.9

## Getting started

`make install` creates the dev environment with:

- a virtualenv in _.venv/_
- pyright in _node_modules/_
- git hooks for formatting & linting on git push

`. .venv/bin/activate` activates the virtualenv.

The make targets will update the virtualenv when _pyproject.toml_ changes.

## Usage

Run `make` to see the options for running tests, linting, formatting etc.

## PRs

Use [conventional commit types](https://www.conventionalcommits.org/en/v1.0.0/) in the PR title. These are used to [label the PR](.github/release-drafter.yml) and categorise the release notes.

## Release

The [Release Drafter workflow](https://github.com/seek-oss/aec/actions/workflows/draft.yml) will automatically create and update a draft release whenever a PR is merged.

To release:

- visit the [release](https://github.com/seek-oss/aec/releases) page and edit the pre-prepared draft release
- check the tag version number and release notes are good to go
- click `Publish release`. This will
  - tag the commit
  - trigger the [CI](https://github.com/seek-oss/aec/actions/workflows/pythonapp.yml) workflow to publish the package to [PyPI](https://pypi.org/project/aec-cli/).
