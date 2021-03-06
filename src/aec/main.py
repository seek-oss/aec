import argparse
import sys
from typing import List

import aec.command.ami as ami
import aec.command.compute_optimizer as compute_optimizer
import aec.command.ec2 as ec2
import aec.command.ssm as ssm
import aec.util.cli as cli
import aec.util.config as config
import aec.util.configure as configure
import aec.util.display as display
from aec.util.cli import Arg, Cmd

config_arg = Arg("--config", help="Section of the config file to use")


def ami_arg_checker(s: str) -> str:
    if not (s.startswith("ami-") or s in ami.ami_keywords.keys()):
        raise argparse.ArgumentTypeError(f"must begin with 'ami-' or be one of {[k for k in ami.ami_keywords.keys()]}")
    return s


# fmt: off

configure_cli = [
    Cmd(configure.example)
]

ec2_cli = [
    Cmd(ec2.describe, [
        config_arg,
        Arg("name", type=str, nargs='?', help="Filter to instances with this Name tag or instance id."),
        Arg("-q", type=str, dest='name_match', help="Filter to instances with a Name tag containing NAME_MATCH."),
        Arg("-r", "--show-running-only", action='store_true', help="Show running or pending instances only"),
        Arg("-it", "--include-terminated", action='store_true', help="Include terminated instances"),
    ]),
    Cmd(ec2.launch, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance"),
        Arg("ami", type=ami_arg_checker, help=f"AMI id or a keyword to lookup the latest ami: {[k for k in ami.ami_keywords.keys()]}"),
        Arg("--volume-size", type=int, help="EBS volume size (GB)", default=100),
        Arg("--encrypted", type=bool, help="Whether the EBS volume is encrypted", default=True),
        Arg("--instance-type", type=str, help="Instance type", default="t2.medium"),
        Arg("--key-name", type=str, help="Key name"),
        Arg("--userdata", type=str, help="Path to user data file")
    ]),
    Cmd(ec2.logs, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance or instance id")
    ]),
    Cmd(ec2.modify, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance or instance id"),
        Arg("type", type=str, help="Type of instance")
    ]),
    Cmd(ec2.start, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance or instance id")
    ]),
    Cmd(ec2.stop, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance or instance id")
    ]),
    Cmd(ec2.terminate, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance or instance id")
    ])
]

ami_cli = [
    Cmd(ami.delete, [
        config_arg,
        Arg("ami", type=str, help="AMI id")
    ]),
    Cmd(ami.describe, [
        config_arg,
        Arg("--ami", type=str, help="Filter to this AMI id"),
        Arg("--owner", type=str, help="Filter to this owning account"),
        Arg("-q", type=str, dest='name_match', help="Filter to images with a name containing NAME_MATCH."),
        Arg("--show-snapshot-id", action='store_true', help="Show snapshot id")
    ]),
    Cmd(ami.share, [
        config_arg,
        Arg("ami", type=str, help="AMI id"),
        Arg("account", type=str, help="Account id"),
    ])
]

compute_optimizer_cli = [
    Cmd(compute_optimizer.over_provisioned, [
        config_arg
    ])
]

ssm_cli = [
    Cmd(ssm.describe, [
        config_arg
    ])
]
# fmt: on


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="aws ec2 cli")
    subparsers = parser.add_subparsers(title="commands")

    cli.add_command_group(subparsers, "configure", "Configure subcommands", configure_cli)
    cli.add_command_group(subparsers, "ec2", "EC2 subcommands", ec2_cli, config.inject_config("~/.aec/ec2.toml"))
    cli.add_command_group(subparsers, "ami", "AMI subcommands", ami_cli, config.inject_config("~/.aec/ec2.toml"))
    cli.add_command_group(
        subparsers,
        "co",
        "Compute optimizer subcommands",
        compute_optimizer_cli,
        config.inject_config("~/.aec/ec2.toml"),
    )
    cli.add_command_group(subparsers, "ssm", "SSM subcommands", ssm_cli, config.inject_config("~/.aec/ec2.toml"))

    return parser


def main(args: List[str] = sys.argv[1:]) -> None:
    result = cli.dispatch(build_parser(), args)
    display.pretty_print(result)


if __name__ == "__main__":
    main()
