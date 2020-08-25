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
    echo "$service"
ls 
    mkdir -p typings/mypy_boto3/"$service"
    mkdir -p typings/mypy_boto3_"$service"
    for f in __init__ client paginator service_resource waiter type_defs; do
        # install generated stubs used by the overloads
        cp "$VIRTUAL_ENV"/lib/python*/site-packages/mypy_boto3/"$service"/$f.py typings/mypy_boto3/"$service"/$f.pyi

        # install packaged stubs for explicit type annotation (also used by the generated stubs)
        cp "$VIRTUAL_ENV"/lib/python*/site-packages/mypy_boto3_"$service"/$f.py typings/mypy_boto3_"$service"/$f.pyi
    done
done


# for service in $VIRTUAL_ENV/lib/python*/site-packages/mypy_boto3_*/
# do
#     case $service in
#         *.dist-info/) ;; # ignore
#         *) basename $service
#     esac
# done

# exit 0






# mkdir -p typings/mypy_boto3_ec2
# for f in __init__ client paginator service_resource waiter type_defs; do
#     cp "$VIRTUAL_ENV"/lib/python*/site-packages/mypy_boto3_ec2/$f.py typings/mypy_boto3_ec2/$f.pyi
# done