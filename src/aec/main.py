from __future__ import annotations

import argparse
import sys
import traceback

import botocore.exceptions

import aec.command.ami as ami
import aec.command.compute_optimizer as compute_optimizer
import aec.command.ec2 as ec2
import aec.command.ssm as ssm
import aec.util.cli as cli
import aec.util.config as config
import aec.util.configure as configure
import aec.util.display as display
from aec.util.cli import Arg, Cmd, parameter_defaults
from aec.util.errors import HandledError

config_arg = Arg("--config", help="Section of the config file to use")


def ami_arg_checker(s: str) -> str:
    if not (s.startswith("ami-") or s in ami.ami_keywords):
        raise argparse.ArgumentTypeError(f"must begin with 'ami-' or be one of {list(ami.ami_keywords.keys())}")

    return s


def tag_arg_checker(tag: str) -> str:
    parts = tag.split("=")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Invalid tag argument '{tag}'. Must be in key=value form.")

    return tag


def non_empty(s: str) -> str:
    if not s:
        raise argparse.ArgumentTypeError("is empty string.")
    return s


# fmt: off

configure_cli = [
    Cmd(configure.example)
]

ec2_cli = [
    Cmd(ec2.create_key_pair, [
        config_arg,
        Arg("key_name", type=str, help="Key pair name"),
        Arg("file_path", type=str,help="Path of private key to create, eg: ~/.ssh/topsecret.pem"),
    ]),
    Cmd(ec2.describe, [
        config_arg,
        Arg("idents", type=non_empty, nargs="*", help="Filter to instances with these Name tags or instance ids."),
        Arg("-q", type=str, dest='name_match', help="Filter to instances with a Name tag containing NAME_MATCH."),
        Arg("-r", "--show-running-only", action='store_true', help="Show running or pending instances only"),
        Arg("-it", "--include-terminated", action='store_true', help="Include terminated instances"),
        Arg("-s", "--sort-by", type=str, help="Sort by one or more fields", default=parameter_defaults(ec2.describe)["sort_by"]),
        Arg("-c", "--columns", type=str, help="Customise the columns shown", default=parameter_defaults(ec2.describe)["columns"]),
    ]),
    Cmd(ec2.launch, [
        config_arg,
        Arg("name", type=str, help="Name tag of instance"),
        Arg("-a", "--ami", type=ami_arg_checker, help=f"AMI id or a keyword to lookup the latest ami: {list(ami.ami_keywords.keys())}"),
        Arg("-t", "--template", type=str, help="Launch template name"),
        Arg("--volume-size", type=int, help="EBS volume size (GB). Defaults to AMI volume size."),
        Arg("--encrypted", type=bool, help="Whether the EBS volume is encrypted", default=True),
        Arg("--instance-type", type=str, help="Instance type"),
        Arg("-k", "--key-name", type=str, help="Key name"),
        Arg("--userdata", type=str, help="User data file path or http URL"),
        Arg("-w", "--wait-ssm", action='store_true', help="Wait until the SSM agent is online before exiting"),
    ]),
    Cmd(ec2.logs, [
        config_arg,
        Arg("ident", type=non_empty, help="Name tag of instance or instance id")
    ]),
    Cmd(ec2.modify, [
        config_arg,
        Arg("ident", type=non_empty, help="Name tag of instance or instance id"),
        Arg("type", type=str, help="Type of instance")
    ]),
    Cmd(ec2.start, [
        config_arg,
        Arg("idents", type=non_empty, nargs="+", help="Name tags of instances or instance ids"),
        Arg("-w", "--wait-ssm", action='store_true', help="Wait until the SSM agent is online before exiting"),
    ]),
    Cmd(ec2.stop, [
        config_arg,
        Arg("idents", type=non_empty, nargs="+", help="Name tags of instances or instance ids")
    ]),
    Cmd(ec2.restart, [
        config_arg,
        Arg("ident", type=non_empty, help="Name tag of instance or instance id"),
        Arg("-t", "--type", type=str, help="Modify the instance to the given type"),
        Arg("-w", "--wait-ssm", action='store_true', help="Wait until the SSM agent is online before exiting"),
    ]),
    Cmd(ec2.sec_groups, [
        config_arg,
        Arg("-v", "--vpc-id", help="Filter to these VPCs"),
    ]),
    Cmd(ec2.subnets, [
        config_arg,
        Arg("-v", "--vpc-id", help="Filter to these VPCs"),
    ]),
    Cmd(ec2.rename, [
        config_arg,
        Arg("ident", type=non_empty, help="Name tag of instance or instance id"),
        Arg("new_name", type=str, help="New name"),
    ]),
    Cmd(ec2.tag, [
        config_arg,
        Arg("ident", type=non_empty, nargs="?", help="Filter to instances with this Name tag or instance id."),
        Arg("-q", type=str, dest='name_match', help="Filter to instances with a Name tag containing NAME_MATCH."),
        Arg("-t", "--tags", type=tag_arg_checker, action="append", metavar="TAG", help="Tags to create in key=value form. This flag can be repeated multiple times.", default = [], required = True),
    ]),
    Cmd(ec2.describe_tags, [
        config_arg,
        Arg("ident", type=non_empty, nargs="?", help="Filter to instances with this Name tag or instance id."),
        Arg("-q", type=str, dest='name_match', help="Filter to instances with a Name tag containing NAME_MATCH."),
        Arg("-v", "--volumes", action='store_true', help="Show volumes"),
        Arg("-k", "--keys", type=str, action="append", metavar="KEY", help="Filter tags to display. This flag can be repeated multiple times.", default = []),
    ], name = "tags"),
    Cmd(ec2.status, [
        config_arg,
        Arg("ident", type=non_empty, nargs="?", help="Filter to instances with this Name tag or instance id."),
        Arg("-q", type=str, dest='name_match', help="Filter to instances with a Name tag containing NAME_MATCH."),
    ]),
    Cmd(ec2.templates, [
        config_arg
    ]),
    Cmd(ec2.terminate, [
        config_arg,
        Arg("idents", type=non_empty, nargs="+", help="Name tags of instances or instance ids"),
        Arg("-y", "--yes", action='store_true', help="Confirm termination without prompting")
    ]),
    Cmd(ec2.user_data, [
        config_arg,
        Arg("ident", type=non_empty, help="Name tag of instance or instance id"),
    ]),
]

ami_cli = [
    Cmd(ami.delete, [
        config_arg,
        Arg("ami", type=str, help="AMI id")
    ]),
    Cmd(ami.describe, [
        config_arg,
        Arg("ident", type=non_empty, nargs="?", help="Filter to this AMI name or id"),
        Arg("--owner", type=str, help="Filter to this owning account"),
        Arg("-q", type=str, dest='name_match', help="Filter to images with a name containing NAME_MATCH."),
        Arg("--show-snapshot-id", action='store_true', help="Show snapshot id")
    ]),
    Cmd(ami.describe_tags, [
        config_arg,
        Arg("ident", type=non_empty, nargs="?", help="Filter to this AMI id"),
        Arg("--owner", type=str, help="Filter to this owning account"),
        Arg("-q", type=str, dest='name_match', help="Filter to images with a name containing NAME_MATCH."),
        Arg("-k", "--keys", type=str, action="append", metavar="KEY", help="Filter tags to display. This flag can be repeated multiple times.", default = []),
    ], name = "tags"),
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
    Cmd(ssm.commands, [
        config_arg,
        Arg("ident", type=non_empty, nargs="?", help="Filter to instances with this Name tag or instance id."),
    ]),
    Cmd(ssm.compliance_summary, [
        config_arg
    ]),
    Cmd(ssm.describe, [
        config_arg,
        Arg("ident", type=non_empty, nargs="?", help="Filter to instances with this Name tag or instance id."),
        Arg("-q", type=str, dest='name_match', help="Filter to instances with a Name tag containing NAME_MATCH."),
    ]),
    Cmd(ssm.invocations, [
        config_arg,
        Arg("command_id", type=str, help="Command id"),
    ]),
    Cmd(ssm.output, [
        config_arg,
        Arg("command_id", type=str, help="Command id"),
        Arg("instance_id", type=str, help="Instance id"),
        Arg("-e", "--stderr", action='store_true', help="Show stderr instead of stdout"),
    ]),
    Cmd(ssm.patch, [
        config_arg,
        Arg("operation", type=str, choices=["scan", "install"], help="Scan or install"),
        Arg("idents", type=str, nargs="+", help="Name tag of instance or instance id. Use 'all' for all running instances"),
        Arg("-nr","--no-reboot", action='store_true', help="Do not reboot after install"),
    ]),
    Cmd(ssm.patch_summary, [
        config_arg
    ]),
    Cmd(ssm.run, [
        config_arg,
        Arg("idents", type=str, nargs="+", help="Name tags of instance or instance ids. Use 'all' for all running instances.")
    ]),
]
# fmt: on


def build_parser() -> argparse.ArgumentParser:
    # prog=aec so that we run in cog the program name isn't cog
    parser = argparse.ArgumentParser(prog="aec", description="aws ec2 cli")
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


def main(args: list[str] = sys.argv[1:]) -> None:
    try:
        result, output_format = cli.dispatch(build_parser(), args)
        display.pretty_print(result, output_format)
    except botocore.exceptions.ClientError as e:
        code = e.response["Error"]["Code"]

        if code == "UnauthorizedOperation":
            message = e.response["Error"]["Message"]
            print(f"{code}: {message}\n\nAuthenticate with the appropriate AWS role before retrying.", file=sys.stderr)
        elif code == "RequestExpired":
            print(
                f"{code}: AWS session token expired.\n\nRe-authenticate with the appropriate AWS role.", file=sys.stderr
            )
        else:
            traceback.print_exc(file=sys.stderr)

    except botocore.exceptions.NoCredentialsError as e:
        print(
            f"NoCredentialsError: {e}.\n\nAuthenticate with the appropriate AWS role before retrying.", file=sys.stderr
        )
    except botocore.exceptions.NoRegionError as e:
        print(f"NoRegionError: {e}\n\nAuthenticate with the appropriate AWS role before retrying.", file=sys.stderr)

    except RuntimeError as e:
        if "Credentials were refreshed" in e.args[0]:
            print(f"RuntimeError: {e.args[0]}\n\nRe-authenticate with the appropriate AWS role.", file=sys.stderr)
        else:
            traceback.print_exc(file=sys.stderr)

    except HandledError as e:
        print(e, file=sys.stderr)


if __name__ == "__main__":
    main()
