from typing import Any, Dict, List, Optional, TYPE_CHECKING
from typing_extensions import Literal

import boto3
import json
import uuid
import sys

import codecs

from botocore.exceptions import ClientError
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
                    "Installed": i["InstalledCount"],
                    "Needed": i["MissingCount"],
                    "Errored": i["FailedCount"],
                    "Pending Reboot": i["InstalledPendingRebootCount"],
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


def patch(
    config: Config, operation: Literal["scan", "install"], names: List[str], no_reboot: bool
) -> List[Dict[str, Optional[str]]]:
    """Scan or install AWS patch baseline"""

    instance_ids = fetch_instance_ids(config, names)

    client = boto3.client("ssm", region_name=config.get("region", None))

    kwargs: Dict[str, Any] = {
        "DocumentName": "AWS-RunPatchBaseline",
        "InstanceIds": instance_ids,
    }

    if operation == "scan":
        kwargs["Parameters"] = {"Operation": ["Scan"], "SnapshotId": [str(uuid.uuid4())]}
    else:
        kwargs["Parameters"] = {
            "Operation": ["Install"],
            "RebootOption": ["NoReboot" if no_reboot else "RebootIfNeeded"],
            "SnapshotId": [str(uuid.uuid4())],
        }

    try:
        kwargs["OutputS3BucketName"] = config["ssm"]["s3bucket"]
        kwargs["OutputS3KeyPrefix"] = config["ssm"]["s3prefix"]
    except KeyError:
        pass

    response = client.send_command(**kwargs)

    return [
        {
            "CommandId": response["Command"]["CommandId"],
            "InstanceId": i,
            "Status": response["Command"]["Status"],
            "Document": response["Command"]["DocumentName"],
            "Output": f"s3://{response['Command']['OutputS3BucketName']}/{response['Command']['OutputS3KeyPrefix']}"
            if response["Command"].get("OutputS3BucketName", None)
            else None,
        }
        for i in response["Command"]["InstanceIds"]
    ]


def run(config: Config, names: List[str]) -> List[Dict[str, Optional[str]]]:
    """Run shell script on instance(s). Script is read from stdin."""

    instance_ids = fetch_instance_ids(config, names)

    client = boto3.client("ssm", region_name=config.get("region", None))

    script = sys.stdin.readlines()

    kwargs: Dict[str, Any] = {
        "DocumentName": "AWS-RunShellScript",
        "InstanceIds": instance_ids,
        "Parameters": {"commands": script},
    }

    try:
        kwargs["OutputS3BucketName"] = config["ssm"]["s3bucket"]
        kwargs["OutputS3KeyPrefix"] = config["ssm"]["s3prefix"]
    except KeyError:
        pass

    response = client.send_command(**kwargs)

    return [
        {
            "CommandId": response["Command"]["CommandId"],
            "InstanceId": i,
            "Status": response["Command"]["Status"],
            "Document": response["Command"]["DocumentName"],
            "Output": f"s3://{response['Command']['OutputS3BucketName']}/{response['Command']['OutputS3KeyPrefix']}"
            if response["Command"].get("OutputS3BucketName", None)
            else None,
        }
        for i in response["Command"]["InstanceIds"]
    ]


def commands(config: Config, name: str) -> List[Dict[str, Optional[str]]]:
    """Commands run on an instance"""

    client = boto3.client("ssm", region_name=config.get("region", None))

    instance_id = fetch_instance_id(config, name)

    response = client.list_commands(InstanceId=instance_id)

    return [
        {
            "RequestedDateTime": c["RequestedDateTime"].strftime("%Y-%m-%d %H:%M"),
            "CommandId": c["CommandId"],
            "Status": c["Status"],
            "DocumentName": c["DocumentName"],
            "Parameters": json.dumps(c["Parameters"]),
            "Output": f"s3://{c['OutputS3BucketName']}/{c['OutputS3KeyPrefix']}"
            if c.get("OutputS3BucketName", None)
            else None,
        }
        for c in response["Commands"]
    ]


def invocations(config: Config, command_id: str) -> List[Dict[str, Optional[str]]]:
    """Invocations across instances for a command"""

    client = boto3.client("ssm", region_name=config.get("region", None))

    command = client.list_commands(CommandId=command_id)["Commands"][0]
    invocations = client.list_command_invocations(CommandId=command_id)

    return [
        {
            "RequestedDateTime": i["RequestedDateTime"].strftime("%Y-%m-%d %H:%M"),
            "InstanceId": i["InstanceId"],
            "Status": i["Status"],
            "DocumentName": i["DocumentName"],
            "Parameters": json.dumps(command["Parameters"]),
            "Output": f"s3://{command['OutputS3BucketName']}/{command['OutputS3KeyPrefix']}"
            if command.get("OutputS3BucketName", None)
            else None,
        }
        for i in invocations["CommandInvocations"]
    ]


DOC_PATHS = {"AWS-RunPatchBaseline": "PatchLinux", "AWS-RunShellScript": "0.awsrunShellScript"}


def output(config: Config, command_id: str, instance_id: str, stderr: bool) -> None:
    """Fetch output of command from S3"""
    ssm_client = boto3.client("ssm", region_name=config.get("region", None))

    command = ssm_client.list_commands(CommandId=command_id)["Commands"][0]

    if not command.get("OutputS3BucketName", None):
        raise ValueError("No OutputS3BucketName")

    bucket = command["OutputS3BucketName"]

    doc_path = DOC_PATHS[command["DocumentName"]]
    std = "stderr" if stderr else "stdout"
    key = f"{command['OutputS3KeyPrefix']}/{command_id}/{instance_id}/awsrunShellScript/{doc_path}/{std}"

    s3_client = boto3.client("s3", region_name=config.get("region", None))

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise KeyError(f"s3://{bucket}/{key} does not exist")
        else:
            raise e

    # converts body bytes to string lines
    for line in codecs.getreader("utf-8")(response["Body"]):
        print(line, end="")

    return None


def fetch_instance_id(config: Config, name: str) -> str:
    if name.startswith("i-"):
        return name

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))
    response = ec2_client.describe_instances(Filters=[{"Name": "tag:Name", "Values": [name]}])

    try:
        return response["Reservations"][0]["Instances"][0]["InstanceId"]
    except IndexError as e:
        raise ValueError(f"No instance named {name}")


def fetch_instance_ids(config: Config, ids_or_names: List[str]) -> List[str]:
    if ids_or_names == ["all"]:
        return [i["ID"] for i in describe(config)]

    ids: List[str] = []
    names: List[str] = []

    for i in ids_or_names:
        if i.startswith("i-"):
            ids.append(i)
        else:
            names.append(i)

    if names:
        ec2_client = boto3.client("ec2", region_name=config.get("region", None))
        response = ec2_client.describe_instances(Filters=[{"Name": "tag:Name", "Values": names}])

        for i in response["Reservations"][0]["Instances"]:
            ids.append(i["InstanceId"])

    return ids


def describe_instances_names(config: Config) -> Dict[str, Optional[str]]:
    """List EC2 instance names in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances()

    return {i["InstanceId"]: util_tags.get_value(i, "Name") for r in response["Reservations"] for i in r["Instances"]}
