import pytest
from moto import mock_ec2
from moto.ec2.models.amis import AMIS

from aec.command.ami import delete, describe, share


@pytest.fixture
def mock_aws_config():
    mock = mock_ec2()
    mock.start()

    return {
        "region": "ap-southeast-2",
    }


def test_describe_images(mock_aws_config):
    # describe images defined by moto
    # see https://github.com/spulec/moto/blob/master/moto/ec2/resources/amis.json
    canonical_account_id = "099720109477"
    mock_aws_config["describe_images_owners"] = canonical_account_id
    images = describe(config=mock_aws_config)

    assert len(images) == 2
    assert images[0]["Name"] == "ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-20170727"
    assert images[1]["Name"] == "ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20170721"


def test_describe_images_by_id(mock_aws_config):
    # describe images defined by moto
    # see https://github.com/spulec/moto/blob/master/moto/ec2/resources/amis.json
    canonical_account_id = "099720109477"
    mock_aws_config["describe_images_owners"] = canonical_account_id
    images = describe(config=mock_aws_config, id="ami-1e749f67")

    assert len(images) == 1


def test_describe_images_name_match(mock_aws_config):
    # describe images defined by moto
    # see https://github.com/spulec/moto/blob/master/moto/ec2/resources/amis.json
    canonical_account_id = "099720109477"
    mock_aws_config["describe_images_owners"] = canonical_account_id
    images = describe(config=mock_aws_config, name_match="*trusty*")

    assert len(images) == 1
    assert images[0]["Name"] == "ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-20170727"


def test_delete_image(mock_aws_config):
    delete(mock_aws_config, AMIS[0]["ami_id"])


def test_share_image(mock_aws_config):
    share(mock_aws_config, AMIS[0]["ami_id"], "123456789012")
