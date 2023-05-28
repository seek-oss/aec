import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""

    # avoid stale creds causing
    # RuntimeError: Credentials were refreshed, but the refreshed credentials are still expired.
    if "AWS_CREDENTIAL_EXPIRATION" in os.environ:
        del os.environ["AWS_CREDENTIAL_EXPIRATION"]
