# use backported importlib_resources for compatability with python < 3.9
from importlib_resources.abc import Traversable
import importlib_resources as resources

import os
import shutil


def example() -> None:
    """create example config files in ~/.aec/."""

    config_dir = os.path.expanduser("~/.aec/")
    if not os.path.exists(config_dir):
        os.mkdir(config_dir)

    for r in resources.files("aec.config-example").iterdir():
        copy(r, config_dir)


def copy(res: Traversable, dest_dir: str) -> None:
    if res.name.startswith("__"):
        return
    elif res.is_file():
        with resources.as_file(res) as file:
            dest_file = f"{dest_dir}{res.name}"
            if os.path.exists(dest_file):
                print(f"Skipping {dest_file} (already exists)")
            else:
                print(f"Writing {dest_file}")
                shutil.copy(file, dest_dir)
    elif res.is_dir():
        subdir = f"{dest_dir}{res.name}/"
        if not os.path.exists(subdir):
            os.mkdir(subdir)
        for r in res.iterdir():
            copy(r, subdir)
