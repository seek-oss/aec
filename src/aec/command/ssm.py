from typing import Any, Dict, List, Optional, TYPE_CHECKING

import boto3

import aec.util.tags as util_tags
from aec.util.config import Config

if TYPE_CHECKING:
    from mypy_boto3_ec2.type_defs import FilterTypeDef


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
    """Describe patch summary for all instances"""
    instances_names = describe_instances_names(config)
    instance_ids = list(instances_names.keys())

    client = boto3.client("ssm", region_name=config.get("region", None))

    max_at_a_time = 50
    result = []
    for i in range(0, len(instance_ids), max_at_a_time):
        chunk = instance_ids[i : i + max_at_a_time]
        response = client.describe_instance_patch_states(InstanceIds=chunk)
        result.extend(
            [
                {
                    "InstanceId": i["InstanceId"],
                    "Name": instances_names.get(i["InstanceId"], None),
                    "Updates installed": i["InstalledCount"],
                    "Updates needed": i["MissingCount"],
                    "Updates with errors": i["FailedCount"],
                    "Last operation time": i["OperationEndTime"],
                    "Last operation": i["Operation"],
                }
                for i in response["InstancePatchStates"]
            ]
        )

    return result


def compliance_summary(config: Config) -> List[Dict[str, Any]]:
    """Describe compliance summary for running instances"""
    instances_names = describe_instances_names(config)

    client = boto3.client("ssm", region_name=config.get("region", None))

    response = client.list_resource_compliance_summaries(
        Filters=[{"Key": "ComplianceType", "Values": ["Patch"], "Type": "EQUAL"}]
    )

    return [
        {
            "InstanceId": i["ResourceId"],
            "Name": instances_names.get(i["ResourceId"], None),
            "Status": i["Status"],
            "NonCompliantCount": i["NonCompliantSummary"]["NonCompliantCount"],
            "Last operation time": i["ExecutionSummary"]["ExecutionTime"],
        }
        for i in response["ResourceComplianceSummaryItems"]
    ]


def patch(config: Config, name: str, operation: str) -> List[Dict[str, str]]:
    """Patch baseline"""

    # TODO add s3 bucket

    filters: List[FilterTypeDef] = []
    if name.startswith("i-"):
        filters = [{"Name": "instance-id", "Values": [name]}]
    else:
        filters = [{"Name": "tag:Name", "Values": [name]}]

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))
    response = ec2_client.describe_instances(Filters=filters)

    instance_id = response["Reservations"][0]["Instances"][0]["InstanceId"]

    client = boto3.client("ssm", region_name=config.get("region", None))

    response = client.send_command(
        DocumentName="AWS-RunPatchBaseline", Parameters={"Operation": [operation]}, InstanceIds=[instance_id]
    )

    return [{
        "CommandId": response["Command"]["CommandId"],
        "InstanceIds": ",".join(response["Command"]["InstanceIds"]),
        "Status": response["Command"]["Status"],
    }]


def describe_instances_names(config: Config) -> Dict[str, Optional[str]]:
    """List EC2 instance names in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances()

    return {i["InstanceId"]: util_tags.get_value(i, "Name") for r in response["Reservations"] for i in r["Instances"]}
