import inspect
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace, _SubParsersAction
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

import tools.config as config


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
