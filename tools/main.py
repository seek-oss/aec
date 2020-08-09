import argparse
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from typing import List

import tools.cli as cli
import tools.configure as configure
import tools.display as display
import tools.ec2 as ec2
import tools.sqs as sqs
from tools.cli import Arg, Cmd

config_arg = Arg("--config", help="Section of the config file to use")

# fmt: off

configure_cli = [
    Cmd(configure.example)
]

ec2_cli = [
    Cmd(ec2.delete_image, [
        config_arg,
        Arg("ami", help="AMI id")
    ]),
    Cmd(ec2.describe, [
        config_arg,
        Arg("--name", help="filter to hosts with this Name tag")
    ]),
    Cmd(ec2.describe_images, [
        config_arg,
        Arg("--ami", help="filter to this AMI id")
    ]),
    Cmd(ec2.launch, [
        config_arg,
        Arg("name", help="Name tag of instance"),
        Arg("ami", help="AMI id"),
        Arg("--dist", help="linux distribution", choices=ec2.root_devices.keys(), default="amazon"),
        Arg("--volume-size", help="ebs volume size (GB)", default=100),
        Arg("--instance-type", help="instance type", default="t2.medium"),
        Arg("--key-name", help="key name"),
        Arg("--userdata", help="path to user data file")   
    ]),
    Cmd(ec2.modify, [
        config_arg,
        Arg("name", help="Name tag of instance"),
        Arg("type", help="type of instance")
    ]),
    Cmd(ec2.share_image, [
        config_arg,
        Arg("ami", help="AMI id"),
        Arg("account", help="account id"),
    ]), 
    Cmd(ec2.start, [
        config_arg,
        Arg("name", help="Name tag of instance")
    ]),
    Cmd(ec2.stop, [
        config_arg,
        Arg("name", help="Name tag of instance")
    ]),
    Cmd(ec2.terminate, [
        config_arg,
        Arg("name", help="Name tag of instance")
    ])
]

sqs_cli = [
    Cmd(sqs.drain, [
        config_arg,
        Arg("file_name", help="file to write messages to"),
        Arg("--keep", help="keep messages, don't delete them", default=False)
    ])
]
# fmt: on


def build_parser() -> ArgumentParser:
    parser = argparse.ArgumentParser(description="aws easy cli", formatter_class=ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers(title="commands")

    cli.add_command_group(subparsers, "configure", "configure subcommands", configure_cli)
    cli.add_command_group(subparsers, "ec2", "ec2 subcommands", ec2_cli, cli.inject_config("~/.aec/ec2.toml"))
    cli.add_command_group(subparsers, "sqs", "sqs subcommands", sqs_cli, cli.inject_config("~/.aec/sqs.toml"))

    return parser


def main(args: List[str] = sys.argv[1:]) -> None:
    result = cli.dispatch(build_parser(), args)
    print(display.prettify(result))


if __name__ == "__main__":
    main()
