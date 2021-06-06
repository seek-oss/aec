import os.path
from argparse import Namespace
from typing import Any, Callable, Dict, Optional

import pytoml as toml
from typing_extensions import TypedDict


class SsmConfig(TypedDict, total=False):
    s3bucket: str
    s3prefix: str


class VpcConfig(TypedDict, total=False):
    name: str
    subnet: str
    security_group: str


class Config(TypedDict, total=False):
    ssm: SsmConfig
    vpc: VpcConfig
    key_name: str
    # the following fields are optional
    region: str
    additional_tags: Dict[str, str]
    iam_instance_profile_arn: str
    kms_key_id: str
    describe_images_owners: str
    describe_images_name_match: str


def inject_config(config_file: str) -> Callable[[Namespace], None]:
    """Replace the "config" arg value with a dict loaded from the config file."""

    def inner(namespace: Namespace) -> None:
        # replace the "config" arg value with a dict loaded from the config file
        if "config" in namespace:
            setattr(namespace, "config", load_config(config_file, namespace.config))

    return inner


# TODO add tests for this
def load_config(config_file: str, profile_override: Optional[str] = None) -> Config:
    """
    Load profile from the config file.

    :param config_file: path to config file
    :param profile_override: override the value of the default profile in the config file
    :raises Exception: if problem loading the config
    :return: config dictionary
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


def load_user_config_file(config_filepath: str) -> Dict[str, Any]:
    if not os.path.isfile(config_filepath):
        raise Exception(f"No config file {config_filepath}")

    with open(config_filepath) as config_file:
        return toml.load(config_file)
