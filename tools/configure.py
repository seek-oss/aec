import os
import shutil
from importlib import resources

from tools.cli import Cmd

namespace_kwargs = {"title": "configure commands", "description": "create config files in ~/.aec/"}


def example():
    """create example config files."""

    with resources.path("tools", "config-example") as example_path:
        config_dir = os.path.expanduser("~/.aec/")
        shutil.copytree(example_path, config_dir)

    print("Created example config in", config_dir)


# fmt: off
cli = [
    Cmd("example", example)
]
# fmt: on
