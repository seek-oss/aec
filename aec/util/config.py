import os.path
from argparse import Namespace
from typing import Any, Callable, Dict, Optional

import pytoml as toml


def inject_config(config_file: str) -> Callable[[Namespace], None]:
    """Replace the "config" arg value with a dict loaded from the config file."""

    def inner(namespace: Namespace) -> None:
        # replace the "config" arg value with a dict loaded from the config file
        if "config" in namespace:
            setattr(namespace, "config", load_config(config_file, namespace.config))

    return inner


# TODO add tests for this
def load_config(config_file: str, profile_override: Optional[str] = None):
    """
    Load profile from the config file.

    :param config_file:
    :param profile_override: override the value of the default profile in the config file
    :return:
    """
    config_filepath = os.path.expanduser(config_file)
    config = load_user_config_file(config_filepath)

    profile = profile_override
    if not profile:
        # set prof to the value of the default key
        if "default_profile" not in config:
            raise Exception(f"No profile override supplied, or default profile set in {config_filepath}")
        profile = config["default_profile"]

    # make top level keys available in the profile
    if config.get("additional_tags", None):
        config[profile]["additional_tags"] = config["additional_tags"]

    try:
        return config[profile]
    except KeyError:
        raise Exception(f"Missing profile {profile_override} in {config_filepath}")


def load_user_config_file(config_filepath) -> Dict[str, Any]:
    if not os.path.isfile(config_filepath):
        raise Exception(f"No config file {config_filepath}")

    with open(config_filepath) as config_file:
        return toml.load(config_file)
