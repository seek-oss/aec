include *.mk

## generate docs
docs: $(venv)
	$(venv)/bin/cog -r docs/*.md
# trim trailing whitespace so hooks are happy
	$(venv)/bin/pre-commit run --files docs/* --hook-stage push trailing-whitespace > /dev/null || true


## test the wheel is correctly packaged
test-dist: tmp_dir:=$(shell mktemp -d)
test-dist: $(venv)
	$(venv)/bin/python3 -m venv --clear $(tmp_dir)
	$(tmp_dir)/bin/pip install dist/*.whl
	$(tmp_dir)/bin/aec ec2 -h

## list outdated packages
outdated: $(venv)
	$(venv)/bin/pip list --outdated
	npm outdated

