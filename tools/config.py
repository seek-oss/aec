import os.path
import sys
from typing import Dict, Any

import pytoml as toml


# TODO add tests for this
def load_config(config_file: str, profile: str = "default"):
    """
    Load profile from the config file.

    :param config_file:
    :param profile: If default, use the value of the default key in the config file
    :return:
    """
    config_filepath = os.path.expanduser(f'~/.aec/{config_file}.toml')
    config = load_user_config_file(config_filepath)

    # set profile to the value of the default key
    if profile == "default":
        profile = config['default_profile']

    # make top level keys available in the profile
    if config.get('additional_tags', None):
        config[profile]['additional_tags'] = config['additional_tags']

    try:
        return config[profile]
    except KeyError:
        print(f"Missing profile {profile} in {config_filepath}", file=sys.stderr)
        exit(1)


def load_user_config_file(config_filepath) -> Dict[str, Any]:
    if not os.path.isfile(config_filepath):
        print(f"WARNING: No file {config_filepath}", file=sys.stderr)
        return {}

    with open(config_filepath) as config_file:
        return toml.load(config_file)
