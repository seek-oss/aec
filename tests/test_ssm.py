from __future__ import annotations

import io

import boto3
import pytest
from moto.ec2.models.amis import AMIS
from mypy_boto3_ec2 import EC2Client
from pytest import MonkeyPatch

from aec.command.ssm import commands, fetch_instance_ids, run
from aec.util.config import Config

# NB: moto provides limited coverage of the SSM API so there's not many tests here
# see https://github.com/spulec/moto/blob/master/IMPLEMENTATION_COVERAGE.md


@pytest.fixture
def mock_aws_config(_mock_ec2: None, _mock_ssm: None):
    return {
        "region": "ap-southeast-2",
    }


def run_instances(client: EC2Client, name: str | None = None) -> str:
    if not name:
        return client.run_instances(ImageId=AMIS[0]["ami_id"], MinCount=1, MaxCount=1)["Instances"][0]["InstanceId"]
    return client.run_instances(
        ImageId=AMIS[0]["ami_id"],
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": name}]}],
    )["Instances"][0]["InstanceId"]


def test_fetch_instance_ids(mock_aws_config: Config):
    client = boto3.client("ec2", region_name=mock_aws_config["region"])
    instance1 = run_instances(client)
    instance2 = run_instances(client, "alice")
    instance3 = run_instances(client)
    instance4 = run_instances(client, "alex")

    assert fetch_instance_ids(mock_aws_config, [instance1, "alice", instance3, "alex"]) == [
        instance1,
        # NB: fetch_instance_ids does not preserve order
        instance3,
        instance2,
        instance4,
    ]


@pytest.mark.skip(reason="failing because of https://github.com/spulec/moto/issues/5424")
def test_run_and_list(mock_aws_config: Config, monkeypatch: MonkeyPatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("ls"))
    run(mock_aws_config, ["alice"])

    results = list(commands(mock_aws_config))

    print(results)

    assert len(results) == 1
    assert results[0]["Status"] == "Success"
