import boto3
import pytest
from moto import mock_ec2
from moto.ec2 import ec2_backends
from moto.ec2.models import AMIS

from tools.ec2 import launch, describe, stop, terminate, start


@pytest.fixture
def mock_aws_configs():
    mock = mock_ec2()
    mock.start()
    region = 'ap-southeast-2'

    return {"region": region,
            "additional_tags": { "Owner": "alice@testlab.io", "Project": "test project a"},
            "key_name": "test_key",
            "vpc": {"name": "test vpc", "subnet": next(ec2_backends[region].get_all_subnets()).id,
                    "security_group": "default"},
            "iam_instance_profile_arn": "test_profile"}


def test_launch(mock_aws_configs):
    print(launch(mock_aws_configs, "alice", AMIS[0]["ami_id"]))


def test_launch_has_userdata(mock_aws_configs):
    print(launch(mock_aws_configs, "test_userdata", AMIS[0]["ami_id"], userdata="conf/userdata/amzn-install-docker.yaml"))


def test_describe(mock_aws_configs):
    launch(mock_aws_configs, "alice", AMIS[0]["ami_id"])
    launch(mock_aws_configs, "sam", AMIS[0]["ami_id"])

    instances = describe(config=mock_aws_configs)
    print(instances)

    assert len(instances) == 2
    assert instances[0]["Name"] == "alice"
    assert instances[1]["Name"] == "sam"


def test_describe_instance_without_tags(mock_aws_configs):
    # create instance without tags
    ec2_client = boto3.client('ec2', region_name=mock_aws_configs['region'])
    ec2_client.run_instances(MaxCount=1, MinCount=1)

    instances = describe(config=mock_aws_configs)
    print(instances)

    assert len(instances) == 1


def test_describe_by_name(mock_aws_configs):
    launch(mock_aws_configs, "alice", AMIS[0]["ami_id"])

    instances = describe(name="alice", config=mock_aws_configs)
    print(instances)

    assert len(instances) == 1
    assert instances[0]["Name"] == "alice"


def test_stop_start(mock_aws_configs):
    launch(mock_aws_configs, "alice", AMIS[0]["ami_id"])

    stop(mock_aws_configs, name="alice")

    start(mock_aws_configs, name="alice")


def test_terminate(mock_aws_configs):
    launch(mock_aws_configs, "alice", AMIS[0]["ami_id"])

    response = terminate(mock_aws_configs, name="alice")

    print(response)
