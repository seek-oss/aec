import pytest
from moto import mock_ec2
from moto.ec2.models import ec2_backends
from moto.ec2.models.amis import AMIS

from aec.command.compute_optimizer import describe_instances_uptime
from aec.command.ec2 import launch
from aec.util.config import Config


@pytest.fixture
def mock_aws_config():
    mock = mock_ec2()
    mock.start()
    region = "us-east-1"

    return {
        "region": region,
        "additional_tags": {"Owner": "alice@testlab.io", "Project": "test project a"},
        "key_name": "test_key",
        "vpc": {
            "name": "test vpc",
            "subnet": ec2_backends["123456789012"]["us-east-1"].get_default_subnet("us-east-1a").id,
            "security_group": "default",
        },
    }


def test_describe_instances_uptime(mock_aws_config: Config):
    launch(mock_aws_config, "alice", AMIS[0]["ami_id"])
    describe_instances_uptime(mock_aws_config)
