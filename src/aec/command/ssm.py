from __future__ import annotations

import codecs
import sys
import uuid
from typing import IO, TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Sequence, TypeVar, Union, cast

import boto3
from botocore.exceptions import ClientError
from typing_extensions import Literal, TypedDict

from aec.util.config import Config
from aec.util.ec2 import describe_instances_names, describe_running_instances_names

if TYPE_CHECKING:
    from mypy_boto3_ssm.type_defs import InstanceInformationStringFilterTypeDef


class Agent(TypedDict):
    ID: str
    Name: Optional[str]
    PingStatus: str
    Platform: str
    AgentVersion: Optional[str]


def describe(
    config: Config,
    name: Optional[str] = None,
    name_match: Optional[str] = None,
) -> Iterator[Agent]:
    """List running instances with the SSM agent."""

    instances_names = describe_running_instances_names(config)

    if name:
        filters = name_filters([name])
    elif name_match:
        # unlike ec2 describe_instances, ssm describe_instance_information doesn't
        # support a wildcard name filter. So do the name match here.
        names = [n for n in instances_names.values() if n and name_match in n]
        if not names:
            return
        filters = name_filters(names)
    else:
        filters = []

    kwargs: Dict[str, Any] = {"MaxResults": 50, "Filters": filters}
    client = boto3.client("ssm", region_name=config.get("region", None))
    while True:
        response = client.describe_instance_information(**kwargs)

        for i in response["InstanceInformationList"]:
            a: Agent = {
                "ID": i["InstanceId"],
                "Name": instances_names.get(i["InstanceId"], None),
                "PingStatus": i["PingStatus"],
                "Platform": f'{i["PlatformName"]} {i["PlatformVersion"]}',
                "AgentVersion": i["AgentVersion"],
            }
            yield a

        next_token = response.get("NextToken", None)
        if next_token:
            kwargs["NextToken"] = next_token
        else:
            break


def patch_summary(config: Config) -> Iterator[Dict[str, Any]]:
    """Patch summary for all instances that have run the patch baseline."""
    instances_names = describe_instances_names(config)
    instance_ids = list(instances_names.keys())

    client = boto3.client("ssm", region_name=config.get("region", None))

    max_at_a_time = 50

    for i in range(0, len(instance_ids), max_at_a_time):
        chunk = instance_ids[i : i + max_at_a_time]
        response = client.describe_instance_patch_states(InstanceIds=chunk)
        for i in response["InstancePatchStates"]:
            yield {
                "InstanceId": i["InstanceId"],
                "Name": instances_names.get(i["InstanceId"], None),
                "Needed": i["MissingCount"],
                "Pending Reboot": i["InstalledPendingRebootCount"],
                "Errored": i["FailedCount"],
                "Rejected": i["InstalledRejectedCount"],
                "Last operation time": i["OperationEndTime"],
                "Last operation": i["Operation"],
            }


def compliance_summary(config: Config) -> List[Dict[str, Any]]:
    """Compliance summary for running instances that have run the patch baseline."""
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
    """Scan or install AWS patch baseline."""

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
    """
    Run a shell script on instance(s).

    Script is read from stdin.
    """

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


E = TypeVar("E")


def first(xs: Optional[Sequence[E]]) -> Optional[E]:
    if xs:
        return xs[0]
    else:
        return None


def commands(config: Config, name: Optional[str] = None) -> Iterator[Dict[str, Union[str, int, None]]]:
    """List commands by instance."""

    client = boto3.client("ssm", region_name=config.get("region", None))

    kwargs: Dict[str, Any] = {"MaxResults": 50}

    if name:
        kwargs["InstanceId"] = fetch_instance_id(config, name)

    while True:
        response = client.list_commands(**kwargs)

        for c in response["Commands"]:
            yield {
                "RequestedDateTime": c["RequestedDateTime"].strftime("%Y-%m-%d %H:%M"),
                "CommandId": c["CommandId"],
                "Status": c["Status"],
                "DocumentName": c["DocumentName"],
                "Operation": first(c["Parameters"].get("Operation", None)),
                "# target": c["TargetCount"],
                "# error": c["ErrorCount"],
                "# timeout": c["DeliveryTimedOutCount"],
                "# complete": c["CompletedCount"],
            }

        next_token = response.get("NextToken", None)
        if next_token:
            kwargs["NextToken"] = next_token
        else:
            break


def invocations(config: Config, command_id: str) -> List[Dict[str, Any]]:
    """List invocations of a command across instances."""

    client = boto3.client("ssm", region_name=config.get("region", None))
    region = client.meta.region_name

    command = client.list_commands(CommandId=command_id)["Commands"][0]
    invocations = client.list_command_invocations(CommandId=command_id)
    instances_names = describe_instances_names(config)

    return [
        {
            "RequestedDateTime": i["RequestedDateTime"].strftime("%Y-%m-%d %H:%M"),
            "InstanceId": i["InstanceId"],
            "Name": instances_names.get(i["InstanceId"], None),
            "StatusDetails": i["StatusDetails"],
            "DocumentName": i["DocumentName"],
            "Operation": ",".join(command["Parameters"]["Operation"]),
            "ConsoleLink": f"https://{region}.console.aws.amazon.com/systems-manager/run-command/{command_id}/{i['InstanceId']}?region={region}",  # noqa: E501
        }
        for i in invocations["CommandInvocations"]
    ]


DOC_PATHS = {"AWS-RunPatchBaseline": "PatchLinux", "AWS-RunShellScript": "0.awsrunShellScript"}


def output(config: Config, command_id: str, instance_id: str, stderr: bool) -> None:
    """Fetch output of a command from S3."""
    ssm_client = boto3.client("ssm", region_name=config.get("region", None))

    command = ssm_client.list_commands(CommandId=command_id)["Commands"][0]

    if not command.get("OutputS3BucketName", None):
        raise ValueError("No OutputS3BucketName")

    bucket = command["OutputS3BucketName"]

    try:
        doc_path = DOC_PATHS[command["DocumentName"]]
    except KeyError:
        raise NotImplementedError(
            f"for {command['DocumentName']}. "
            + "Run aws s3 ls {command['OutputS3KeyPrefix']}/{command_id}/{instance_id}/awsrunShellScript/"
        ) from None

    std = "stderr" if stderr else "stdout"
    key = f"{command['OutputS3KeyPrefix']}/{command_id}/{instance_id}/awsrunShellScript/{doc_path}/{std}"

    s3_client = boto3.client("s3", region_name=config.get("region", None))

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise KeyError(f"s3://{bucket}/{key} does not exist") from None
        else:
            raise e

    # converts body bytes to string lines
    streaming_body = cast(IO[bytes], response["Body"])
    for line in codecs.getreader("utf-8")(streaming_body):
        print(line, end="")

    return None


def fetch_instance_id(config: Config, name: str) -> str:
    if name.startswith("i-"):
        return name

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))
    response = ec2_client.describe_instances(Filters=[{"Name": "tag:Name", "Values": [name]}])

    try:
        return response["Reservations"][0]["Instances"][0]["InstanceId"]
    except IndexError:
        raise ValueError(f"No instance named {name}") from None


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

        try:
            for r in response["Reservations"]:
                for i in r["Instances"]:
                    ids.append(i["InstanceId"])
        except IndexError:
            raise ValueError(f"No instances with ids or names {','.join(names)}") from None
    return ids


def name_filters(names_or_ids: Optional[List[str]] = None) -> List[InstanceInformationStringFilterTypeDef]:
    if names_or_ids and names_or_ids[0].startswith("i-"):
        return [{"Key": "InstanceIds", "Values": names_or_ids}]
    elif names_or_ids:
        return [{"Key": "tag:Name", "Values": names_or_ids}]
    else:
        return []
