import os
import shutil

# use importlib_resources backport for compatibility with python < 3.9
import importlib_resources as resources
from importlib_resources.abc import Traversable


def example() -> None:
    """create example config files in ~/.aec/."""

    config_dir = os.path.expanduser("~/.aec/")
    os.makedirs(config_dir, exist_ok=True)

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
        os.makedirs(subdir, exist_ok=True)
        for r in res.iterdir():
            copy(r, subdir)
