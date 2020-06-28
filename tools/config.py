import os.path
import sys
from typing import Any, Dict

import pytoml as toml

Config = Dict[str, Any]

# TODO add tests for this
def load_config(config_file: str, profile: str = "default") -> Config:
    """
    Load profile from the config file.

    :param config_file:
    :param profile: If default, use the value of the default key in the config file
    :return:
    """
    config_filepath = os.path.expanduser(config_file)
    config = load_user_config_file(config_filepath)

    # set profile to the value of the default key
    if profile == "default" or profile is None:
        if "default_profile" not in config:
            print(
                f"No profile supplied, or default profile set in {config_filepath}", file=sys.stderr,
            )
            exit(1)
        profile = config["default_profile"]

    # make top level keys available in the profile
    if config.get("additional_tags", None):
        config[profile]["additional_tags"] = config["additional_tags"]

    try:
        return config[profile]
    except KeyError:
        print(f"Missing profile {profile} in {config_filepath}", file=sys.stderr)
        exit(1)


def load_user_config_file(config_filepath) -> Dict[str, Any]:
    if not os.path.isfile(config_filepath):
        print(f"No config file {config_filepath}", file=sys.stderr)
        exit(1)

    with open(config_filepath) as config_file:
        return toml.load(config_file)
