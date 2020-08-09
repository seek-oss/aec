import inspect
import json
from argparse import Action, ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace, _SubParsersAction
from functools import wraps
from typing import Any, Callable, Optional

import argh

from tools.config import load_config
from tools.display import as_table, pretty_table


class Cli:
    def __init__(
        self, config_file: str, namespace: str, title: Optional[str] = None, description: Optional[str] = None
    ):
        self.namespace = namespace
        self.config_file = config_file
        self.namespace_kwargs = {"title": title, "description": description}
        self.commands = []

    def cmd(self, func: Callable[..., Any]):
        """
        A decorator that defines common args, injects config, and pretty prints the results of the function it wraps
        when called from the CLI. When called by other functions, treat it as usual familiar (undecorated) function call,
        ie: just pass through to the wrapped function. This means we can treat the function as a familiar function,
        and easily provide the extra CLI functionality only when needed.

        :param func:
        :return:
        """

        @wraps(func)
        @argh.arg("--config", help="Section of the config file to use")
        def wrapper(*args, **kwargs):
            # print(args)
            # print(kwargs)

            # config is always the final arg
            CONFIG_ARG_INDEX = 0

            # if arg/kwargs contain the config dict then we are being called from tests,
            # or by other functions, so just pass through
            if (args and isinstance(args[CONFIG_ARG_INDEX], dict)) or isinstance(kwargs.get("config", None), dict):
                return func(*args, **kwargs)

            # here we are being called from the cli

            # load the config and pass it to the function
            profile = args[CONFIG_ARG_INDEX]
            config = load_config(self.config_file, profile)

            args_without_config = args[CONFIG_ARG_INDEX:]
            result = func(*args_without_config, config, **kwargs)

            # prettify the result
            if isinstance(result, list):
                prettified = pretty_table(as_table(result))
                return prettified if prettified else "No results"
            elif isinstance(result, dict):
                return json.dumps(result, default=str)
            else:
                return result

        # prevent argh help from displaying a positional args param
        wrapper.__signature__ = inspect.signature(func)

        self.commands.append(wrapper)

        # TODO: just register and return unwrapped func
        return wrapper


from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Any, Callable, List


class Arg:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


@dataclass
class Cmd:
    name: str
    func: Callable[..., Any]
    help: str
    args: Optional[List[Arg]] = None


def usage_exit(parser: ArgumentParser) -> Callable[[Namespace], None]:
    def inner(args: Namespace) -> None:
        parser.print_usage()
        parser.exit(1, "{}: no subcommand specified\n".format(parser.prog))

    return inner


def add_command_group(parent: _SubParsersAction, name: str, help: str, cmds: List[Cmd]) -> None:
    group = parent.add_parser(name, help=help)
    # show help if no args provided to the command group
    group.set_defaults(func=usage_exit(group))
    subcommands = group.add_subparsers()

    for cmd in cmds:
        parser = subcommands.add_parser(cmd.name, help=cmd.help, formatter_class=ArgumentDefaultsHelpFormatter)
        if cmd.args:
            for arg in cmd.args:
                parser.add_argument(*arg.args, **arg.kwargs)
