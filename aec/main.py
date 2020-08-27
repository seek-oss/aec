import argparse
import sys
from typing import List

import aec.command.compute_optimizer as compute_optimizer
import aec.command.ssm as ssm
import aec.command.ec2 as ec2
import aec.command.sqs as sqs
import aec.util.cli as cli
import aec.util.config as config
import aec.util.configure as configure
import aec.util.display as display
from aec.util.cli import Arg, Cmd

config_arg = Arg("--config", help="Section of the config file to use")

# fmt: off

configure_cli = [
    Cmd(configure.example)
]

ec2_cli = [
    Cmd(ec2.delete_image, [
        config_arg,
        Arg("ami", type=str, help="AMI id")
    ]),
    Cmd(ec2.describe, [
        config_arg,
        Arg("--name", type=str, help="Filter to hosts with this Name tag")
    ]),
    Cmd(ec2.describe_images, [
        config_arg,
        Arg("--ami", type=str, help="Filter to this AMI id")
    ]),
    Cmd(ec2.launch, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance"),
        Arg("ami", type=str, help="AMI id"),
        Arg("--dist", type=str, help="Linux distribution", choices=ec2.root_devices.keys(), default="amazon"),
        Arg("--volume-size", type=int, help="EBS volume size (GB)", default=100),
        Arg("--encrypted", type=bool, help="Whether the EBS volume is encrypted", default=True),
        Arg("--instance-type", type=str, help="Instance type", default="t2.medium"),
        Arg("--key-name", type=str, help="Key name"),
        Arg("--userdata", type=str, help="Path to user data file")
    ]),
    Cmd(ec2.modify, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance"),
        Arg("type", type=str, help="Type of instance")
    ]),
    Cmd(ec2.share_image, [
        config_arg,
        Arg("ami", type=str, help="AMI id"),
        Arg("account", type=str, help="Account id"),
    ]),
    Cmd(ec2.start, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance")
    ]),
    Cmd(ec2.stop, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance")
    ]),
    Cmd(ec2.terminate, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance")
    ])
]

sqs_cli = [
    Cmd(sqs.drain, [
        config_arg,
        Arg("file_name", type=str, help="File to write messages to"),
        Arg("--keep", type=str, help="Keep messages, don't delete them", default=False)
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
    parser = argparse.ArgumentParser(description="aws easy cli")
    subparsers = parser.add_subparsers(title="commands")

    cli.add_command_group(subparsers, "configure", "Configure subcommands", configure_cli)
    cli.add_command_group(subparsers, "ec2", "EC2 subcommands", ec2_cli, config.inject_config("~/.aec/ec2.toml"))
    cli.add_command_group(subparsers, "sqs", "SQS subcommands", sqs_cli, config.inject_config("~/.aec/sqs.toml"))
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
