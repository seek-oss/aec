import boto3
import pytest
from moto.ec2.models.amis import AMIS
from mypy_boto3_ec2 import EC2Client
from mypy_boto3_ec2.type_defs import TagTypeDef

from aec.command.ami import delete, describe, describe_tags, share
from aec.util.config import Config


@pytest.fixture
def mock_aws_config(_mock_ec2: None) -> Config:
    return {
        "region": "ap-southeast-2",
    }


def test_describe_images(mock_aws_config: Config):
    # describe images defined by moto
    # see https://github.com/spulec/moto/blob/master/moto/ec2/resources/amis.json
    canonical_account_id = "099720109477"
    mock_aws_config["describe_images_owners"] = canonical_account_id
    images = describe(config=mock_aws_config)

    assert len(images) == 2
    assert {i["Name"] for i in images} == {
        "ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-20170727",
        "ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20170721",
    }


def test_describe_images_by_id(mock_aws_config: Config):
    # describe images defined by moto
    # see https://github.com/spulec/moto/blob/master/moto/ec2/resources/amis.json
    canonical_account_id = "099720109477"
    mock_aws_config["describe_images_owners"] = canonical_account_id
    images = describe(config=mock_aws_config, idents="ami-1e749f67")
    assert len(images) == 1

    images = describe(config=mock_aws_config, idents=["ami-1e749f67", "ami-785db401"])
    assert len(images) == 2


def test_describe_images_by_name(mock_aws_config: Config):
    # describe images defined by moto
    # see https://github.com/spulec/moto/blob/master/moto/ec2/resources/amis.json
    canonical_account_id = "099720109477"
    mock_aws_config["describe_images_owners"] = canonical_account_id
    images = describe(config=mock_aws_config, idents="ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-20170727")
    assert len(images) == 1

    images = describe(
        config=mock_aws_config,
        idents=[
            "ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-20170727",
            "ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20170721",
        ],
    )

    assert len(images) == 2


def test_describe_images_name_match(mock_aws_config: Config):
    # describe images defined by moto
    # see https://github.com/spulec/moto/blob/master/moto/ec2/resources/amis.json
    canonical_account_id = "099720109477"
    mock_aws_config["describe_images_owners"] = canonical_account_id
    images = describe(config=mock_aws_config, name_match="*trusty*")

    assert len(images) == 1
    assert images[0]["Name"] == "ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-20170727"


def test_tags_image(mock_aws_config: Config):
    ec2_client: EC2Client = boto3.client("ec2", region_name=mock_aws_config["region"])

    response = ec2_client.run_instances(MaxCount=1, MinCount=1)
    instance_id = response["Instances"][0]["InstanceId"]

    tags: list[TagTypeDef] = [{"Key": "Team", "Value": "Engineering"}, {"Key": "Source AMI", "Value": "ami-12345"}]

    ec2_client.create_image(
        InstanceId=instance_id, Name="Beautiful Image", TagSpecifications=[{"ResourceType": "image", "Tags": tags}]
    )

    images = describe_tags(config=mock_aws_config)

    assert len(images) == 1
    assert images[0]["Tags"] == "Team=Engineering, Source AMI=ami-12345"

    images = describe_tags(config=mock_aws_config, keys=["Team", "Source AMI"])

    assert len(images) == 1
    assert images[0]["Tag: Team"] == "Engineering"
    assert images[0]["Tag: Source AMI"] == "ami-12345"


def test_describe_tags_two_image_ids(mock_aws_config: Config):
    # describe images defined by moto
    # see https://github.com/spulec/moto/blob/master/moto/ec2/resources/amis.json
    canonical_account_id = "099720109477"
    mock_aws_config["describe_images_owners"] = canonical_account_id

    ec2_client: EC2Client = boto3.client("ec2", region_name=mock_aws_config["region"])

    # Add tags to the existing moto AMIs
    tags1: list[TagTypeDef] = [{"Key": "Team", "Value": "Engineering"}, {"Key": "Environment", "Value": "Prod"}]
    ec2_client.create_tags(Resources=["ami-1e749f67"], Tags=tags1)

    tags2: list[TagTypeDef] = [{"Key": "Team", "Value": "Sales"}, {"Key": "Environment", "Value": "Dev"}]
    ec2_client.create_tags(Resources=["ami-785db401"], Tags=tags2)

    # Test describe_tags with both image IDs
    images = describe_tags(config=mock_aws_config, idents=["ami-1e749f67", "ami-785db401"])

    assert len(images) == 2
    assert images[0]["ImageId"] == "ami-1e749f67"
    assert images[1]["ImageId"] == "ami-785db401"
    assert images[0]["Tags"] == "Team=Engineering, Environment=Prod"
    assert images[1]["Tags"] == "Team=Sales, Environment=Dev"


def test_delete_image(mock_aws_config: Config):
    delete(mock_aws_config, AMIS[0]["ami_id"])


def test_share_image(mock_aws_config: Config):
    share(mock_aws_config, AMIS[0]["ami_id"], "123456789012")
