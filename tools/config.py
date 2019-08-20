import sys

import pytoml as toml
import os.path
from typing import Dict, Any

config_filepath = os.path.expanduser('~/.aww/config')


def load_config(profile: str = "default"):
    config = load_user_config_file()
    if profile == "default":
        profile = config[profile]

    try:
        return config[profile]
    except KeyError:
        print(f"Missing profile {profile} in {config_filepath}", file=sys.stderr)
        exit(1)


def load_user_config_file() -> Dict[str, Any]:
    if not os.path.isfile(config_filepath):
        print(f"WARNING: No file {config_filepath}", file=sys.stderr)
        return {}

    with open(config_filepath) as config_file:
        return toml.load(config_file)
