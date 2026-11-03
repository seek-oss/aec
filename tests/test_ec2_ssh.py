import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from aec.main import main


def _install_ssh_stub(tmp_path: Path, mocker: MockerFixture) -> Path:
    capture_path = tmp_path / "ssh-args.json"
    ssh_path = tmp_path / "ssh"
    ssh_path.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['SSH_ARGS_FILE'], 'w') as capture:\n"
        "    json.dump(sys.argv[1:], capture)\n"
    )
    ssh_path.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    env["SSH_ARGS_FILE"] = str(capture_path)

    def execvp(file: str, args: list[str]) -> None:
        assert file == "ssh"
        subprocess.run(args, check=True, env=env)

    mocker.patch("aec.command.ec2.os.execvp", side_effect=execvp)
    return capture_path


def _instance(public_dns_name: str) -> dict[str, Any]:
    return {
        "InstanceId": "i-0123456789abcdef0",
        "State": {"Name": "running"},
        "Tags": [{"Key": "Name", "Value": "alice"}],
        "PublicDnsName": public_dns_name,
        "PrivateIpAddress": "10.0.0.12",
    }


def test_ssh_without_arguments_shows_usage(capsys: pytest.CaptureFixture[str], mocker: MockerFixture):
    load_config = mocker.patch("aec.util.config.load_config")
    execvp = mocker.patch("aec.command.ec2.os.execvp")

    with pytest.raises(SystemExit) as exit_info:
        main(["ec2", "ssh"])

    output = capsys.readouterr().out
    assert exit_info.value.code == 0
    assert output.splitlines()[0] == (
        "usage: aec ec2 ssh [--config PROFILE] -- [SSH_OPTIONS ...] [username@]EC2_NAME [REMOTE_COMMAND ...]"
    )
    load_config.assert_not_called()
    execvp.assert_not_called()


@pytest.mark.parametrize(
    ("public_dns_name", "destination_arg", "expected_destination"),
    [
        (
            "ec2-203-0-113-12.compute-1.amazonaws.com",
            "ubuntu@alice",
            "ubuntu@ec2-203-0-113-12.compute-1.amazonaws.com",
        ),
        ("", "ubuntu@alice", "ubuntu@10.0.0.12"),
        ("ec2-203-0-113-12.compute-1.amazonaws.com", "alice", "ec2-203-0-113-12.compute-1.amazonaws.com"),
    ],
    ids=["public-dns-user", "no-public-dns-uses-private-ip", "public-dns-bare-name"],
)
def test_ssh_resolves_instance_and_preserves_ssh_arguments(
    public_dns_name: str,
    destination_arg: str,
    expected_destination: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
):
    capture_path = _install_ssh_stub(tmp_path, mocker)
    ec2_client = mocker.Mock()
    ec2_client.describe_instances.return_value = {"Reservations": [{"Instances": [_instance(public_dns_name)]}]}
    mocker.patch("aec.command.ec2.boto3.client", return_value=ec2_client)
    mocker.patch("aec.util.config.load_config", return_value={"region": "us-east-1"})

    main(
        [
            "ec2",
            "ssh",
            "--config",
            "production",
            "--",
            "-i",
            "~/.ssh/alice",
            "-o",
            "ProxyCommand=nc -X 5 proxy.example 22",
            destination_arg,
            "uptime",
        ]
    )

    assert json.loads(capture_path.read_text()) == [
        "-i",
        "~/.ssh/alice",
        "-o",
        "ProxyCommand=nc -X 5 proxy.example 22",
        expected_destination,
        "uptime",
    ]
    assert capsys.readouterr().err == (
        f"ssh -i '~/.ssh/alice' -o 'ProxyCommand=nc -X 5 proxy.example 22' {expected_destination} uptime\n"
    )
    ec2_client.describe_instances.assert_called_once()
    assert ec2_client.describe_instances.call_args.kwargs["Filters"] == [{"Name": "tag:Name", "Values": ["alice"]}]


def test_ssh_reports_when_instance_name_does_not_match(capsys: pytest.CaptureFixture[str], mocker: MockerFixture):
    ec2_client = mocker.Mock()
    ec2_client.describe_instances.return_value = {"Reservations": []}
    mocker.patch("aec.command.ec2.boto3.client", return_value=ec2_client)
    mocker.patch("aec.util.config.load_config", return_value={"region": "us-east-1"})
    execvp = mocker.patch("aec.command.ec2.os.execvp")

    main(["ec2", "ssh", "--", "ubuntu@missing"])

    assert "No instances with name missing" in capsys.readouterr().err
    execvp.assert_not_called()
