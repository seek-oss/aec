import json
from functools import wraps

from argh import arg

from tools.config import load_config
from tools.display import pretty_table, as_table


def cli(func):
    """
    A decorator that defines common args, injects config, and pretty prints the results of the function it wraps
    when called from the CLI. When called by other functions, treat it as usual familiar (undecorated) function call,
    ie: just pass through to the wrapped function. This means we can treat the function as a familiar function,
    and easily provide the extra CLI functionality only when needed.

    :param func:
    :return:
    """

    @wraps(func)
    @arg("--profile", help="Profile in the config file to use", default="default")
    def wrapper(*args, **kwargs):
        #print(args)
        #print(kwargs)

        # we are being called from tests, or by other functions, just pass through
        if args or 'config' in kwargs:
            return func(*args, **kwargs)

        # we are being called from the cli, so load the config and prettify the result
        profile = kwargs.pop('profile', 'default')
        kwargs['config'] = load_config(profile)

        result = func(*args, **kwargs)

        if isinstance(result, list):
            prettified = pretty_table(as_table(result))
            return prettified if prettified else "No results"
        elif isinstance(result, dict):
            return json.dumps(result, default=str)
        else:
            return result

    return wrapper
