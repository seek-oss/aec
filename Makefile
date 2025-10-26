include *.mk

## generate docs
.PHONY: docs
docs:
	COLUMNS=100 uv run cog -r docs/*.md
# trim trailing whitespace so hooks are happy
	uv run prek run --files docs/* --hook-stage pre-push > /dev/null || true

## test the wheel is correctly packaged
test-dist: tmp_dir:=$(shell mktemp -d)
test-dist:
	uv run python3 -m venv --clear $(tmp_dir)
	$(tmp_dir)/bin/pip install dist/*.whl
	$(tmp_dir)/bin/aec ec2 -h

## list outdated packages
outdated:
	uv run pip list --outdated

