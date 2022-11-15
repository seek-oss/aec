from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Sequence

import boto3

from aec.util.config import Config
from aec.util.ec2_types import DescribeArgs

if TYPE_CHECKING:
    from mypy_boto3_ec2.type_defs import InstanceTypeDef, VolumeTypeDef


def get_value(instance: InstanceTypeDef | VolumeTypeDef, key: str) -> Optional[str]:
    tag_value = [t["Value"] for t in instance.get("Tags", []) if t["Key"] == key]
    return tag_value[0] if tag_value else None


def describe_running_instances_names(config: Config) -> Dict[str, Optional[str]]:
    # 2x speed up (8 -> 4 secs) compared to listing all names
    return describe_instances_names(config, {"instance-state-name": ["running"]})


def describe_instances_names(
    config: Config, filters: Optional[Dict[str, Sequence[str]]] = None
) -> Dict[str, Optional[str]]:
    """Map of EC2 instance ids to names in the region."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    kwargs: DescribeArgs = {"MaxResults": 1000}
    if filters:
        kwargs["Filters"] = [{"Name": k, "Values": v} for k, v in filters.items()]

    instances: Dict[str, Optional[str]] = {}

    while True:
        response = ec2_client.describe_instances(**kwargs)

        for r in response["Reservations"]:
            for i in r["Instances"]:
                instance_id = i["InstanceId"]
                instances[instance_id] = get_value(i, "Name")

        next_token = response.get("NextToken", None)
        if next_token:
            kwargs["NextToken"] = next_token
        else:
            break

    return instances
