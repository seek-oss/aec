from __future__ import annotations

import io
from contextlib import redirect_stdout
from typing import Any, Dict, Iterator, List

from moto import mock_ec2
from moto.ec2 import ec2_backends
from moto.ec2.models.amis import AMIS

import aec.command.ec2 as ec2
import aec.util.display as display
from aec.util.config import Config

# fixtures
mock_ec2().start()
region = "ap-southeast-2"
mock_aws_config: Config = {
    "region": region,
    "key_name": "test_key",
    "vpc": {
        "name": "test vpc",
        "subnet": next(ec2_backends[region].get_all_subnets()).id,
        "security_group": "default",
    },
    "iam_instance_profile_arn": "test_profile",
}
ami_id = AMIS[0]["ami_id"]

ec2.launch(mock_aws_config, "alice", ami_id)
ec2.launch(mock_aws_config, "sam", ami_id)


def docs(
    cmd_name: str,
    result: List[Dict[str, Any]] | Iterator[Dict[str, Any]] | Dict | str | None,
) -> str:
    capture = io.StringIO()
    with redirect_stdout(capture):
        display.pretty_print(result)
    return f"{cmd_name}\n{capture.getvalue().rstrip()}"
