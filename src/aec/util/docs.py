from aec.util.config import Config
from moto import mock_ec2
from moto.ec2.models.amis import AMIS
from moto.ec2 import ec2_backends
import aec.command.ec2 as ec2
import aec.util.display as display
from contextlib import redirect_stdout
import io

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


def describe():
    capture = io.StringIO()
    with redirect_stdout(capture):
        result = ec2.describe(mock_aws_config)
        display.pretty_print(result)
    return capture.getvalue()
