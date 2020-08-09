import argparse
import sys
from argparse import Action, ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace, _SubParsersAction
from typing import Callable, List

import argh

import tools.cli
import tools.configure
import tools.ec2
import tools.sqs
from tools.cli import Cmd


def help_func(parser: ArgumentParser) -> Callable[[Namespace], None]:
    def print_help(args: Namespace) -> None:
        parser.print_help()

    return print_help


def add_subparser(subparsers: _SubParsersAction, name: str, title: str, cmds: List[Cmd]) -> None:
    parser = subparsers.add_parser(name, help=title)
    tools.cli.add_args(parser, cmds)
    # show help if no args provided to the command
    parser.set_defaults(func=help_func(parser))


def build_parser() -> ArgumentParser:
    parser = argparse.ArgumentParser(description="aws easy cli", formatter_class=ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers()

    add_subparser(subparsers, "ec2", "ec2 commands", tools.ec2.cli2)
    add_subparser(subparsers, "configure", "configure commands", tools.configure.cli)

    return parser


def main(args: List[str] = sys.argv[1:]) -> None:
    parser = build_parser()

    ## dispatch

    parsed_args = parser.parse_args(args)
    v = vars(parsed_args)
    if not v.get("func"):
        parser.print_usage()
        parser.exit(1, "{}: no command specified\n".format(parser.prog))
    parsed_args.func(parsed_args)

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
