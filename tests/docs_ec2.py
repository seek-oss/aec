from moto import mock_ec2
from moto.ec2 import ec2_backends
from moto.ec2.models.amis import AMIS

from aec import main
from aec.command.ec2 import describe, launch

ami_id = AMIS[0]["ami_id"]


def mock_aws_config():
    mock = mock_ec2()
    mock.start()
    region = "us-east-1"

    return {
        "region": region,
        "key_name": "test_key",
        "vpc": {
            "name": "test vpc",
            "subnet": next(ec2_backends[region].get_all_subnets()).id,
            "security_group": "default",
        },
        "iam_instance_profile_arn": "test_profile",
    }


def describe(config):
    launch(config, "alice", ami_id)
    launch(config, "sam", ami_id)

    main.main(["ec2", "status"])


if __name__ == "__main__":
    describe(mock_aws_config())
