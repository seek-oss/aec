import inspect
import json
from argparse import Action, ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace, _SubParsersAction
from functools import wraps
from typing import Any, Callable, Optional

import argh

import tools.config as config
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
    # dispatch to this function
    call_me: Callable[..., Any]
    args: Optional[List[Arg]] = None
    name: Optional[str] = None
    help: Optional[str] = None

    def __post_init__(self):
        if self.name is None:
            self.name = self.call_me.__name__.replace("_", "-")
        if self.help is None:
            # use call_me's docstring for help
            self.help = inspect.getdoc(self.call_me)

        # check all args are specified
        call_me_num_args = len(inspect.signature(self.call_me).parameters)
        if self.args and len(self.args) != call_me_num_args:
            raise Exception(
                f"{self.call_me.__name__} has {call_me_num_args} args but {len(self.args)} defined for the cli"
            )
        elif not self.args and call_me_num_args > 0:
            raise Exception(f"{self.call_me.__name__} has {call_me_num_args} args but none defined for the cli")
        # inspect.signature(call_me)


def usage_exit(parser: ArgumentParser) -> Callable[[], None]:
    def inner() -> None:
        parser.print_usage()
        parser.exit(1, "{}: no subcommand specified\n".format(parser.prog))

    return inner


def add_command_group(
    parent: _SubParsersAction,
    name: str,
    help: str,
    cmds: List[Cmd],
    args_pre_processor: Optional[Callable[[Namespace], None]] = None,
) -> None:
    group = parent.add_parser(name, help=help)
    # show help if no args provided to the command group
    group.set_defaults(call_me=usage_exit(group))
    if args_pre_processor:
        group.set_defaults(args_pre_processor=args_pre_processor)
    subcommands = group.add_subparsers(title="subcommands")

    for cmd in cmds:
        parser = subcommands.add_parser(
            cmd.name, help=cmd.help, description=cmd.help, formatter_class=ArgumentDefaultsHelpFormatter
        )
        parser.set_defaults(call_me=cmd.call_me)
        if cmd.args:
            for arg in cmd.args:
                parser.add_argument(*arg.args, **arg.kwargs)


def prettify(result):
    """prettify, instead of showing a dict, or list of dicts."""
    if isinstance(result, list):
        prettified = pretty_table(as_table(result))
        return prettified if prettified else "No results"
    elif isinstance(result, dict):
        return json.dumps(result, default=str)
    else:
        return result


def inject_config(config_file: str) -> Callable[[Namespace], None]:
    def inner(namespace: Namespace) -> None:
        # replace the "config" arg value with a dict loaded from the config file
        if "config" in namespace:
            setattr(namespace, "config", config.load_config(config_file, namespace.config))

    return inner


def dispatch(parser: ArgumentParser, args: List[str]) -> Any:
    pargs = parser.parse_args(args)

    if "args_pre_processor" in pargs:
        pargs.args_pre_processor(pargs)
        delattr(pargs, "args_pre_processor")

    if "call_me" not in pargs:
        parser.print_usage()
        parser.exit(1, "{}: no command specified\n".format(parser.prog))

    call_me = pargs.call_me
    # remove call_me arg because call_me doesn't expect it
    delattr(pargs, "call_me")
    return call_me(**vars(pargs))
