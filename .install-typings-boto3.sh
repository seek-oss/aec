#!/usr/bin/env bash

set -uoe pipefail

function die() {
    >&2 echo -e "$@"
    exit 1
}

[[ -z "${VIRTUAL_ENV:-}" ]] && die "Please activate the virtualenv first"

"$VIRTUAL_ENV"/bin/python -m mypy_boto3

# workaround for https://github.com/vemel/mypy_boto3_builder/issues/39
# install overloads for implicit type inference on boto3.client/boto3.resource
mkdir -p typings/boto3
cp "$VIRTUAL_ENV"/lib/python*/site-packages/mypy_boto3/boto3_init_gen.py typings/boto3/__init__.pyi

for d in "$VIRTUAL_ENV"/lib/python*/site-packages/mypy_boto3/[!_]*/
do
    service=$(basename "$d")
    echo "Installing pyright stubs into typings/ for $service"
 
    mkdir -p typings/mypy_boto3/"$service"
    mkdir -p typings/mypy_boto3_"$service"
    for f in "$VIRTUAL_ENV"/lib/python*/site-packages/mypy_boto3/"$service"/*.py; do
        module=$(basename -s .py "$f")

        # install generated stubs used by the overloads
        cp "$VIRTUAL_ENV"/lib/python*/site-packages/mypy_boto3/"$service"/"$module".py typings/mypy_boto3/"$service"/"$module".pyi

        # install packaged stubs for explicit type annotation (also used by the generated stubs)
        cp "$VIRTUAL_ENV"/lib/python*/site-packages/mypy_boto3_"$service"/"$module".py typings/mypy_boto3_"$service"/"$module".pyi
    done
done