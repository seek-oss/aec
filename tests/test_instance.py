from tools.instance import launch
from moto import mock_ec2


@mock_ec2
def test_launch():
    launch("test", "alice@testlab.io")
