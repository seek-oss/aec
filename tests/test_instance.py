import boto3
import pytest
from moto import mock_ec2
from moto.ec2.models import AMIS
from moto.ec2 import ec2_backends

from tools.instance import launch


@mock_ec2
@pytest.fixture(scope="module")
def mock_aws_configs():
    region = 'ap-southeast-2'
    mock = mock_ec2()
    mock.start()

    ec2 = boto3.resource('ec2', region)

    # create VPC
    vpc = ec2.create_vpc(CidrBlock='192.168.0.0/16')
    vpc.wait_until_available()
    print(vpc.id)

    # create subnet
    subnet = ec2.create_subnet(CidrBlock='192.168.1.0/24', VpcId=vpc.id)
    # set subnet state to available
    subnet.reload()
    print(subnet.id)

    # Create sec group
    sec_group = ec2.create_security_group(GroupName='sg_0', Description='sg_0', VpcId=vpc.id)
    print(sec_group.id)

    print(AMIS[0]["ami_id"])
    mock.stop()

    print(ec2_backends[region].subnets)

    configs = {}
    configs[region] = {"amis": {"gami": AMIS[0]["ami_id"]},
                       "key_name": "test_key",
                       "security_group": sec_group.id,
                       "subnet": subnet.id,
                       "iam_instance_profile_arn": "test_profile"}
    return configs


@mock_ec2
def test_launch(mock_aws_configs):
    launch("test", "alice@testlab.io", configs=mock_aws_configs)
