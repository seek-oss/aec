from moto import mock_ec2
from moto.ec2.models.amis import AMIS

from aec import main
from aec.command.ec2 import launch

ami_id = AMIS[0]["ami_id"]

mock = mock_ec2()
mock.start()

launch({"key_name": "test_key"}, "alice", ami_id)
launch({"key_name": "test_key"}, "sam", ami_id)

main.main(["ec2", "status"])
