import pytest
from moto import mock_ec2
from moto.ec2 import ec2_backends
from moto.ec2.models.amis import AMIS

from aec.command.compute_optimizer import describe_instances_uptime
from aec.command.ec2 import launch


@pytest.fixture
def mock_aws_config():
    mock = mock_ec2()
    mock.start()
    region = "ap-southeast-2"

    return {
        "region": region,
        "additional_tags": {"Owner": "alice@testlab.io", "Project": "test project a"},
        "key_name": "test_key",
        "vpc": {
            "name": "test vpc",
            "subnet": next(ec2_backends[region].get_all_subnets()).id,
            "security_group": "default",
        },
        "iam_instance_profile_arn": "test_profile",
    }


def test_describe_instances_uptime(mock_aws_config):
    launch(mock_aws_config, "alice", AMIS[0]["ami_id"])
    describe_instances_uptime(mock_aws_config)
