from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

import boto3

from aec.util.config import Config

if TYPE_CHECKING:
    from mypy_boto3_ec2.type_defs import InstanceTypeDef, VolumeTypeDef


def get_value(instance: InstanceTypeDef | VolumeTypeDef, key: str) -> Optional[str]:
    tag_value = [t["Value"] for t in instance.get("Tags", []) if t["Key"] == key]
    return tag_value[0] if tag_value else None


def describe_instances_names(config: Config) -> Dict[str, Optional[str]]:
    """List EC2 instance names in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances()

    return {i["InstanceId"]: get_value(i, "Name") for r in response["Reservations"] for i in r["Instances"]}
