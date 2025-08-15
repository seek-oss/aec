from __future__ import annotations

from collections.abc import Sequence
from typing import TypedDict

import boto3

import aec.util.tags as util_tags
from aec.util.config import Config
from aec.util.ec2_types import DescribeArgs


class InstanceNameState(TypedDict):
    InstanceId: str
    State: str
    Name: str | None


def describe_running_instances_names(config: Config) -> dict[str, str | None]:
    # 2x speed up (8 -> 4 secs) compared to listing all names
    return describe_instances_names(config, {"instance-state-name": ["running"]})


def describe_instances_names(config: Config, filters: dict[str, Sequence[str]] | None = None) -> dict[str, str | None]:
    """Map of EC2 instance ids to names in the region."""
    instances = describe_instances(config, filters)
    return {id: state["Name"] for id, state in instances.items()}


def describe_instances(config: Config, filters: dict[str, Sequence[str]] | None = None) -> dict[str, InstanceNameState]:
    """Map of EC2 instance ids to InstanceNameState in the region."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    kwargs: DescribeArgs = {"MaxResults": 1000}
    if filters:
        kwargs["Filters"] = [{"Name": k, "Values": v} for k, v in filters.items()]

    instances: dict[str, InstanceNameState] = {}

    while True:
        response = ec2_client.describe_instances(**kwargs)

        for r in response["Reservations"]:
            for i in r["Instances"]:
                instance_id = i["InstanceId"]
                instances[instance_id] = {
                    "InstanceId": instance_id,
                    "State": i.get("State", {}).get("Name", "unknown"),
                    "Name": util_tags.get_value(i, "Name"),
                }

        next_token = response.get("NextToken", None)
        if next_token:
            kwargs["NextToken"] = next_token
        else:
            break

    return instances
