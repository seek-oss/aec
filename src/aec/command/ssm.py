from __future__ import annotations

import codecs
import sys
import uuid
from collections.abc import Iterator, Sequence
from typing import IO, TYPE_CHECKING, Any, TypeVar, cast

import boto3
from botocore.exceptions import ClientError
from typing_extensions import Literal, TypedDict

from aec.util.config import Config
from aec.util.ec2_util import describe_instances, describe_instances_names, describe_running_instances_names

if TYPE_CHECKING:
    from mypy_boto3_ssm.type_defs import InstanceInformationStringFilterTypeDef, ListCommandInvocationsRequestTypeDef


class Agent(TypedDict):
    ID: str
    Name: str | None
    PingStatus: str
    Platform: str
    AgentVersion: str | None


def describe(
    config: Config,
    ident: str | None = None,
    name_match: str | None = None,
) -> Iterator[Agent]:
    """List running instances with the SSM agent."""

    instances_names = describe_running_instances_names(config)

    if ident:
        filters = name_filters([ident])
    elif name_match:
        # unlike ec2 describe_instances, ssm describe_instance_information doesn't
        # support a wildcard name filter. So do the name match here.
        names = [n for n in instances_names.values() if n and name_match in n]
        if not names:
            return
        filters = name_filters(names)
    else:
        filters = []

    kwargs: dict[str, Any] = {"MaxResults": 50, "Filters": filters}
    client = boto3.client("ssm", region_name=config.get("region", None))
    while True:
        response = client.describe_instance_information(**kwargs)

        for i in response["InstanceInformationList"]:
            a: Agent = {
                "ID": i["InstanceId"],
                "Name": instances_names.get(i["InstanceId"], None),
                "PingStatus": i["PingStatus"],
                "Platform": f"{i['PlatformName']} {i['PlatformVersion']}",
                "AgentVersion": i["AgentVersion"],
            }
            yield a

        next_token = response.get("NextToken", None)
        if next_token:
            kwargs["NextToken"] = next_token
        else:
            break


def patch_summary(config: Config) -> Iterator[dict[str, Any]]:
    """Patch summary for all instances that have run the patch baseline."""
    instances = describe_instances(config)
    instance_ids = list(instances.keys())

    client = boto3.client("ssm", region_name=config.get("region", None))

    max_at_a_time = 50

    for i in range(0, len(instance_ids), max_at_a_time):
        chunk = instance_ids[i : i + max_at_a_time]
        response = client.describe_instance_patch_states(InstanceIds=chunk)
        for i in response["InstancePatchStates"]:
            yield {
                "InstanceId": i["InstanceId"],
                "Name": (instances.get(i["InstanceId"], None) or {}).get("Name", None),
                "State": (instances.get(i["InstanceId"], None) or {}).get("State", None),
                "Needed": i["MissingCount"],
                "Pending Reboot": i["InstalledPendingRebootCount"],
                "Errored": i["FailedCount"],
                "Rejected": i["InstalledRejectedCount"],
                "Last operation time": i["OperationEndTime"],
                "Last operation": i["Operation"],
            }


def compliance_summary(config: Config) -> Iterator[dict[str, Any]]:
    """Compliance summary for instances that have run the patch baseline."""
    instances_names = describe_instances_names(config)

    kwargs: dict[str, Any] = {"Filters": [{"Key": "ComplianceType", "Values": ["Patch"], "Type": "EQUAL"}]}
    client = boto3.client("ssm", region_name=config.get("region", None))

    while True:
        response = client.list_resource_compliance_summaries(**kwargs)

        for i in response["ResourceComplianceSummaryItems"]:
            yield {
                "InstanceId": i["ResourceId"],
                "Name": instances_names.get(i["ResourceId"], None),
                "Status": i["Status"],
                "NonCompliantCount": i["NonCompliantSummary"]["NonCompliantCount"],
                "Last operation time": i["ExecutionSummary"].get("ExecutionTime", None),
            }

        next_token = response.get("NextToken", None)
        if next_token:
            kwargs["NextToken"] = next_token
        else:
            break


def patch(
    config: Config, operation: Literal["scan", "install"], idents: list[str], no_reboot: bool
) -> list[dict[str, str | None]]:
    """Scan or install AWS patch baseline."""

    instance_ids = fetch_instance_ids(config, idents)

    client = boto3.client("ssm", region_name=config.get("region", None))

    kwargs: dict[str, Any] = {
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


def run(config: Config, idents: list[str]) -> list[dict[str, str | None]]:
    """
    Run a shell script on instance(s).

    Script is read from stdin.
    """

    instance_ids = fetch_instance_ids(config, idents)

    client = boto3.client("ssm", region_name=config.get("region", None))

    script = sys.stdin.readlines()

    kwargs: dict[str, Any] = {
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


def first(xs: Sequence[E] | None) -> E | None:
    if xs:
        return xs[0]
    else:
        return None


def commands(config: Config, ident: str | None = None) -> Iterator[dict[str, str | int | None]]:
    """List commands by instance."""

    client = boto3.client("ssm", region_name=config.get("region", None))

    kwargs: dict[str, Any] = {"MaxResults": 50}

    if ident:
        kwargs["InstanceId"] = fetch_instance_id(config, ident)

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


def invocations(config: Config, command_id: str) -> Iterator[dict[str, Any]]:
    """List invocations of a command across instances."""

    client = boto3.client("ssm", region_name=config.get("region", None))
    region = client.meta.region_name

    command = client.list_commands(CommandId=command_id)["Commands"][0]
    instances_names = describe_instances_names(config)
    kwargs: ListCommandInvocationsRequestTypeDef = {"CommandId": command_id}

    while True:
        response = client.list_command_invocations(**kwargs)

        for i in response["CommandInvocations"]:
            yield {
                "RequestedDateTime": i["RequestedDateTime"].strftime("%Y-%m-%d %H:%M"),
                "InstanceId": i["InstanceId"],
                "Name": instances_names.get(i["InstanceId"], None),
                "StatusDetails": i["StatusDetails"],
                "DocumentName": i["DocumentName"],
                "Operation": ",".join(command["Parameters"].get("Operation", "")),
                "ConsoleLink": f"https://{region}.console.aws.amazon.com/systems-manager/run-command/{command_id}/{i['InstanceId']}?region={region}",
            }

        next_token = response.get("NextToken", None)
        if next_token:
            kwargs["NextToken"] = next_token
        else:
            break


DOC_PATHS = {"AWS-RunPatchBaseline": "PatchLinux", "AWS-RunShellScript": "0.awsrunShellScript"}


def output(config: Config, command_id: str, ident: str, stderr: bool) -> None:
    """Fetch output of a command from S3."""
    ssm_client = boto3.client("ssm", region_name=config.get("region", None))

    command = ssm_client.list_commands(CommandId=command_id)["Commands"][0]

    if not command.get("OutputS3BucketName", None):
        raise ValueError("No OutputS3BucketName")

    bucket = command["OutputS3BucketName"]

    instance_id = fetch_instance_id(config, ident)

    try:
        doc_path = DOC_PATHS[command["DocumentName"]]
    except KeyError:
        prefix = command.get("OutputS3KeyPrefix", "")
        raise NotImplementedError(
            f"for {command['DocumentName']}. Run aws s3 ls {prefix}/{command_id}/{instance_id}/awsrunShellScript/"
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


def fetch_instance_id(config: Config, ident: str) -> str:
    if ident.startswith("i-"):
        return ident

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))
    response = ec2_client.describe_instances(Filters=[{"Name": "tag:Name", "Values": [ident]}])

    try:
        return response["Reservations"][0]["Instances"][0]["InstanceId"]
    except IndexError:
        raise ValueError(f"No instance named {ident}") from None


def fetch_instance_ids(config: Config, idents: list[str]) -> list[str]:
    if idents == ["all"]:
        return [i["ID"] for i in describe(config)]

    ids: list[str] = []
    names: list[str] = []

    for i in idents:
        if i.startswith("i-"):
            ids.append(i)
        else:
            names.append(i)

    if names:
        ec2_client = boto3.client("ec2", region_name=config.get("region", None))
        response = ec2_client.describe_instances(Filters=[{"Name": "tag:Name", "Values": names}])

        try:
            ids.extend(i["InstanceId"] for r in response["Reservations"] for i in r["Instances"])
        except IndexError:
            raise ValueError(f"No instances with ids or names {','.join(names)}") from None
    return ids


def name_filters(idents: list[str] | None = None) -> list[InstanceInformationStringFilterTypeDef]:
    if idents and idents[0].startswith("i-"):
        return [{"Key": "InstanceIds", "Values": idents}]
    elif idents:
        return [{"Key": "tag:Name", "Values": idents}]
    else:
        return []
