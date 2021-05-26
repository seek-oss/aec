from typing import Any, Dict, List, Optional

import boto3

import aec.util.tags as util_tags
from aec.util.config import Config


def describe(config: Config) -> List[Dict[str, Any]]:
    """Describe instances running the SSM agent."""

    instances_names = describe_instances_names(config)

    client = boto3.client("ssm", region_name=config.get("region", None))

    response = client.describe_instance_information()

    return [
        {
            "ID": i["InstanceId"],
            "Name": instances_names.get(i["InstanceId"], None),
            "PingStatus": i["PingStatus"],
            "Platform": f'{i["PlatformName"]} {i["PlatformVersion"]}',
            "AgentVersion": i["AgentVersion"],
        }
        for i in response["InstanceInformationList"]
    ]


def patch_summary(config: Config) -> List[Dict[str, Any]]:
    """Describe patch summary forlike the AWS console"""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances()

    instance_ids = [i["InstanceId"] for r in response["Reservations"] for i in r["Instances"]]

    client = boto3.client("ssm", region_name=config.get("region", None))

    print(len(instance_ids))

    response = client.describe_instance_patch_states(InstanceIds=instance_ids[:50])

    return [
        {
            "InstanceId": i["InstanceId"],
            "Updates installed": i["InstalledCount"],
            "Updates needed": i["MissingCount"],
            "Updates with errors": i["FailedCount"],
            "Last operation time": i["OperationEndTime"],
            "Last operation": i["Operation"]
        }
        for i in response["InstancePatchStates"]
    ]


def describe_instances_names(config: Config) -> Dict[str, Optional[str]]:
    """List EC2 instance names in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances()

    return {i["InstanceId"]: util_tags.get_value(i, "Name") for r in response["Reservations"] for i in r["Instances"]}
