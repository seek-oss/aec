from typing import Optional

import boto3
import pytest
from moto import mock_ec2
from moto.ec2.models.amis import AMIS

from aec.command.ssm import fetch_instance_ids

# NB: moto provides limited coverage of the SSM API so there's not many tests here
# see https://github.com/spulec/moto/blob/master/IMPLEMENTATION_COVERAGE.md


@pytest.fixture
def mock_aws_config():
    mock = mock_ec2()
    mock.start()

    return {
        "region": "ap-southeast-2",
    }


def run_instances(client, name: Optional[str] = None) -> str:
    if not name:
        return client.run_instances(ImageId=AMIS[0]["ami_id"], MinCount=1, MaxCount=1)["Instances"][0]["InstanceId"]
    return client.run_instances(
        ImageId=AMIS[0]["ami_id"],
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": name}]}],
    )["Instances"][0]["InstanceId"]


def test_fetch_instance_ids(mock_aws_config):
    client = boto3.client("ec2", region_name=mock_aws_config["region"])
    instance1 = run_instances(client)
    instance2 = run_instances(client, "alice")
    instance3 = run_instances(client)
    instance4 = run_instances(client, "alex")

    fetch_instance_ids(mock_aws_config, [instance1, "alice", instance3, "alex"]) == [
        instance1,
        instance2,
        instance3,
        instance4,
    ]
