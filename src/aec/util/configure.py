import os
import shutil
from importlib import resources

namespace_kwargs = {"title": "configure commands", "description": "create config files in ~/.aec/"}


def example() -> None:
    """create example config files in ~/.aec/."""

    with resources.path("aec", "config-example") as example_path:
        config_dir = os.path.expanduser("~/.aec/")
        shutil.copytree(example_path, config_dir)

    print("Created example config in", config_dir)
