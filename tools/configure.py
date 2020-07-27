import os
import shutil

namespace_kwargs = {"title": "configure commands", "description": "create config files in ~/.aec/"}


def example():
    """create example config files."""

    config_dir = os.path.expanduser("~/.aec/")
    shutil.copytree("./config-example", config_dir)

    print("Created example config in", config_dir)
