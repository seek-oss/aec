import json
from functools import wraps

import argh

from display import pretty_table, as_table
from config import load_config


def cli(func):
    """
    A decorator that injects config, and pretty prints the results of the function it wraps

    :param func:
    :return:
    """

    @wraps(func)
    @argh.arg("--profile", help="Profile in the config file to use", default="default")
    def wrapper(*args, **kwargs):
        print(args)
        print(kwargs)
        profile = kwargs.pop('profile', 'default')

        config = load_config(profile)

        result = func(config, *args, **kwargs)

        if isinstance(result, list):
            return pretty_table(as_table(result))
        elif isinstance(result, dict):
            return json.dumps(result)
        else:
            return result

    return wrapper
