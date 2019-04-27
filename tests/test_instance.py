import boto3
import pytest
from moto import mock_ec2
from moto.ec2.models import AMIS
from moto.ec2 import ec2_backends

from tools.instance import launch


@pytest.fixture(scope="module")
def mock_aws_configs():
    mock = mock_ec2()
    mock.start()
    region = 'ap-southeast-2'

    configs = {}
    configs[region] = {"amis": {"gami": AMIS[0]["ami_id"]},
                       "key_name": "test_key",
                       "security_group": "default",
                       "subnet": next(ec2_backends[region].get_all_subnets()).id,
                       "iam_instance_profile_arn": "test_profile"}
    return configs


def test_launch(mock_aws_configs):
    launch("test", "alice@testlab.io", configs=mock_aws_configs)
