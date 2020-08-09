import argparse
import sys
from argparse import Action, ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace, _SubParsersAction
from typing import Callable, List

import argh

import tools.cli as cli
import tools.configure
import tools.ec2
import tools.sqs


def build_parser() -> ArgumentParser:
    parser = argparse.ArgumentParser(description="aws easy cli", formatter_class=ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers()

    cli.add_command_group(subparsers, "ec2", "ec2 commands", tools.ec2.cli2, cli.inject_config("~/.aec/ec2.toml"))
    cli.add_command_group(subparsers, "configure", "configure commands", tools.configure.cli)

    return parser


def main(args: List[str] = sys.argv[1:]) -> None:
    result = cli.dispatch(build_parser(), args)
    print(cli.prettify(result))

    # parser = argh.ArghParser()
    # for cli in [tools.ec2.cli, tools.sqs.cli]:
    #     parser.add_commands(
    #         sorted(cli.commands, key=lambda f: f.__name__),
    #         namespace=cli.namespace,
    #         namespace_kwargs=cli.namespace_kwargs,
    #     )
    # parser.add_commands(
    #     [tools.configure.example], namespace="configure", namespace_kwargs=tools.configure.namespace_kwargs
    # )
    # parser.dispatch()


if __name__ == "__main__":
    main()
