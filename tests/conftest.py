import os

import pytest
from moto import mock_aws
from moto.core.models import DEFAULT_ACCOUNT_ID
from moto.ec2.models import ec2_backends
from moto.ssm.models import ssm_backends


@pytest.fixture(scope="session", autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""

    # avoid stale creds causing
    # RuntimeError: Credentials were refreshed, but the refreshed credentials are still expired.
    if "AWS_CREDENTIAL_EXPIRATION" in os.environ:
        del os.environ["AWS_CREDENTIAL_EXPIRATION"]


@pytest.fixture(scope="session")
def _mock_aws():
    with mock_aws():
        yield


@pytest.fixture
def _mock_ec2(_mock_aws: None):
    yield
    # reset just the ec2 backend because its quicker than resetting all backends
    ec2_backends[DEFAULT_ACCOUNT_ID].reset()


@pytest.fixture
def _mock_ssm(_mock_aws: None):
    yield
    # reset just the ssm backend because its quicker than resetting all backends
    ssm_backends[DEFAULT_ACCOUNT_ID].reset()
