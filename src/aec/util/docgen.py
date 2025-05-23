from __future__ import annotations

import io
import os
from collections.abc import Iterator
from contextlib import redirect_stdout
from typing import Any

from moto import mock_aws
from moto.ec2.models import ec2_backends
from moto.ec2.models.amis import AMIS

import aec.command.ec2 as ec2
import aec.util.display as display
from aec.util.config import Config

# avoid stale creds causing
# RuntimeError: Credentials were refreshed, but the refreshed credentials are still expired.
if "AWS_CREDENTIAL_EXPIRATION" in os.environ:
    del os.environ["AWS_CREDENTIAL_EXPIRATION"]

# fixtures
mock_aws().start()
region = "us-east-1"
mock_aws_config: Config = {
    "region": region,
    "key_name": "test_key",
    "vpc": {
        "name": "test vpc",
        "subnet": ec2_backends["123456789012"]["us-east-1"].get_default_subnets()["us-east-1a"].id,
        "security_group": "default",
    },
}
ami_id = AMIS[0]["ami_id"]

ec2.launch(mock_aws_config, "alice", ami_id)
ec2.launch(mock_aws_config, "sam", ami_id)


def docs(
    cmd_name: str,
    result: list[dict[str, Any]] | Iterator[dict[str, Any]] | dict | str | None,
) -> str:
    capture = io.StringIO()
    with redirect_stdout(capture):
        display.pretty_print(result)
    return f"{cmd_name}\n{capture.getvalue().rstrip()}"
