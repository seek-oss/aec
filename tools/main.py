import argparse
import sys
from argparse import Action, ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from typing import Callable, List

import argh

import tools.cli
import tools.configure
import tools.ec2
import tools.sqs


def help_func(parser: ArgumentParser) -> Callable[[Namespace], None]:
    def print_help(args: Namespace) -> None:
        parser.print_help()

    return print_help


def add_subparser(parser: ArgumentParser) -> Action:
    subparser = parser.add_subparsers()
    help_parser = subparser.add_parser("help", help="show help for this command")
    help_parser.set_defaults(func=help_func(parser))
    return subparser


def build_parser() -> ArgumentParser:
    parser = argparse.ArgumentParser(description="aws easy cli", formatter_class=ArgumentDefaultsHelpFormatter)

    add_subparser(parser)

    tools.cli.add_args(parser, tools.ec2.args)

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
