from __future__ import annotations

import base64
import os
import os.path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, cast

import boto3
from typing_extensions import TypedDict

from aec.util.ec2 import describe_running_instances_names
from aec.util.errors import NoInstancesError
from aec.util.threads import executor

if TYPE_CHECKING:
    from mypy_boto3_ec2.literals import InstanceTypeType
    from mypy_boto3_ec2.type_defs import (
        BlockDeviceMappingTypeDef,
        FilterTypeDef,
        InstanceStatusSummaryTypeDef,
        TagSpecificationTypeDef,
        TagTypeDef,
    )

import aec.command.ami as ami_cmd
import aec.util.ec2 as util_tags
from aec.util.config import Config
from aec.util.ec2_types import RunArgs


def is_ebs_optimizable(instance_type: str) -> bool:
    return not instance_type.startswith("t2")


class Instance(TypedDict, total=False):
    InstanceId: str
    State: str
    Name: Optional[str]
    Type: str
    DnsName: str
    SubnetId: str


def launch(
    config: Config,
    name: str,
    ami: Optional[str] = None,
    template: Optional[str] = None,
    volume_size: Optional[int] = None,
    encrypted: bool = True,
    instance_type: Optional[str] = None,
    key_name: Optional[str] = None,
    userdata: Optional[str] = None,
) -> List[Instance]:
    """Launch a tagged EC2 instance with an EBS volume."""

    template = template or config.get("launch_template", None)

    if not (template or ami):
        raise ValueError("Please specify either an ami or a launch template")

    if not template and not instance_type:
        # if no instance type is provided set one
        instance_type = "t3.small"

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    runargs: RunArgs = {
        "MaxCount": 1,
        "MinCount": 1,
    }

    desc = ""
    if template:
        runargs["LaunchTemplate"] = {"LaunchTemplateName": template}
        desc = f"template {template} "

    if ami:
        image = ami_cmd.fetch(config, ami)
        if not image["RootDeviceName"]:
            raise ValueError(f"{image['ImageId']} is missing RootDeviceName")

        volume_size = volume_size or config.get("volume_size", None) or image["Size"]
        if not volume_size:
            raise ValueError("No volume size")

        device: BlockDeviceMappingTypeDef = {
            "DeviceName": image["RootDeviceName"],
            "Ebs": {
                "VolumeSize": volume_size,
                "DeleteOnTermination": True,
                "VolumeType": "gp3",
                "Encrypted": encrypted,
            },
        }

        kms_key_id = config.get("kms_key_id", None)
        if kms_key_id:
            device["Ebs"]["KmsKeyId"] = kms_key_id

        runargs["ImageId"] = image["ImageId"]
        runargs["BlockDeviceMappings"] = [device]

        desc = desc + image["Name"] if image["Name"] else desc + image["ImageId"]

    key = key_name or config.get("key_name", None)
    if key:
        runargs["KeyName"] = key
    elif not template:
        print(
            "WARNING: You have not specified a key pair.",
            "You will only be able to connect to this instance if it is configured for "
            + "EC2 Instance Connect or Systems Manager Session Manager.",
        )

    if instance_type:
        runargs["InstanceType"] = cast("InstanceTypeType", instance_type)
        runargs["EbsOptimized"] = is_ebs_optimizable(instance_type)

    tags: List[TagTypeDef] = [{"Key": "Name", "Value": name}]
    additional_tags = config.get("additional_tags", {})
    if additional_tags:
        tags.extend([{"Key": k, "Value": v} for k, v in additional_tags.items()])
    runargs["TagSpecifications"] = [
        cast("TagSpecificationTypeDef", {"ResourceType": "instance", "Tags": tags}),
        cast("TagSpecificationTypeDef", {"ResourceType": "volume", "Tags": tags}),
    ]

    if config.get("vpc", None):
        # TODO: support multiple subnets
        security_group = config["vpc"]["security_group"]
        runargs["NetworkInterfaces"] = [
            {
                "DeviceIndex": 0,
                "Description": "Primary network interface",
                "DeleteOnTermination": True,
                "SubnetId": config["vpc"]["subnet"],
                "Ipv6AddressCount": 0,
                "Groups": security_group if isinstance(security_group, list) else [security_group],
            }
        ]
        associate_public_ip_address = config["vpc"].get("associate_public_ip_address", None)
        if associate_public_ip_address is not None:
            runargs["NetworkInterfaces"][0]["AssociatePublicIpAddress"] = associate_public_ip_address

        vpc_name = f" vpc {config['vpc']['name']}"
    else:
        vpc_name = ""

    iam_instance_profile_arn = config.get("iam_instance_profile_arn", None)
    if iam_instance_profile_arn:
        runargs["IamInstanceProfile"] = {"Arn": iam_instance_profile_arn}

    if userdata:
        if userdata.startswith("http://") or userdata.startswith("https://"):
            runargs["UserData"] = read_url(userdata)
        else:
            runargs["UserData"] = read_file(userdata)

    # use IMDSv2 to prevent SSRF
    runargs["MetadataOptions"] = {"HttpTokens": "required"}

    region_name = ec2_client.meta.region_name

    print(
        f"Launching {'a ' + instance_type if instance_type else 'an instance'} in "
        + f"{region_name}{vpc_name} named {name} using {desc} ... "
    )
    response = ec2_client.run_instances(**runargs)

    instance = response["Instances"][0]

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance["InstanceId"]])

    # TODO: wait until instance checks passed (as they do in the console)

    # the response from run_instances above always contains an empty string
    # for PublicDnsName, so we call describe to get it
    return describe(config=config, name=name)


def describe(
    config: Config,
    name: Optional[str] = None,
    name_match: Optional[str] = None,
    include_terminated: bool = False,
    show_running_only: bool = False,
    sort_by: str = "State,Name",
    columns: str = "InstanceId,State,Name,Type,DnsName,LaunchTime,ImageId",
) -> List[Instance]:
    """List EC2 instances in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    filters = name_filters(name, name_match)
    if show_running_only:
        filters.append({"Name": "instance-state-name", "Values": ["pending", "running"]})

    # TODO: handle more than 1000 results by looping using NextToken
    response = ec2_client.describe_instances(MaxResults=1000, Filters=filters)

    # print(response["Reservations"][0]["Instances"][0])

    cols = columns.split(",")

    # don't sort by cols we aren't showing
    sort_cols = [sc for sc in sort_by.split(",") if sc in cols]

    instances: List[Instance] = []
    for r in response["Reservations"]:
        for i in r["Instances"]:
            if include_terminated or i["State"]["Name"] != "terminated":
                desc: Instance = {}

                for col in cols:
                    if col == "State":
                        desc[col] = i["State"]["Name"]
                    elif col == "Name":
                        desc[col] = util_tags.get_value(i, "Name")
                    elif col == "Type":
                        desc[col] = i["InstanceType"]
                    elif col == "DnsName":
                        desc[col] = i["PublicDnsName"] if i.get("PublicDnsName", None) != "" else i["PrivateDnsName"]
                    else:
                        desc[col] = i.get(col, None)

                instances.append(desc)

    return sorted(
        instances,
        key=lambda i: "".join(str(i[field]) for field in sort_cols),
    )


def describe_tags(
    config: Config,
    name: Optional[str] = None,
    name_match: Optional[str] = None,
    keys: Sequence[str] = [],
    volumes: bool = False,
) -> List[Dict[str, Any]]:
    """List EC2 instances or volumes with their tags."""
    if volumes:
        return volume_tags(config, name, name_match, keys)

    return instance_tags(config, name, name_match, keys)


def tag(
    config: Config,
    tags: List[str],
    name: Optional[str] = None,
    name_match: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Tag EC2 instance(s)."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    tagdefs: List[TagTypeDef] = []
    for t in tags:
        parts = t.split("=")
        tagdefs.append({"Key": parts[0], "Value": parts[1]})

    if not name and not name_match:
        # avoid tagging all instances when there's no name
        raise NoInstancesError(name=name, name_match=name_match)

    instances = describe(config, name, name_match)

    ids = [i["InstanceId"] for i in instances]

    if not ids:
        raise NoInstancesError(name=name, name_match=name_match)

    ec2_client.create_tags(Resources=ids, Tags=tagdefs)

    return describe_tags(config, name, name_match, keys=[d["Key"] for d in tagdefs])


def instance_tags(
    config: Config, name: Optional[str] = None, name_match: Optional[str] = None, keys: Sequence[str] = []
) -> List[Dict[str, Any]]:
    """List EC2 instances with their tags."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances(Filters=name_filters(name, name_match))

    instances: List[Dict[str, Any]] = []
    for r in response["Reservations"]:
        for i in r["Instances"]:
            if i["State"]["Name"] != "terminated":
                inst = {"InstanceId": i["InstanceId"], "Name": util_tags.get_value(i, "Name")}
                if not keys:
                    inst["Tags"] = ", ".join(f"{tag['Key']}={tag['Value']}" for tag in i.get("Tags", []))
                else:
                    for key in keys:
                        inst[f"Tag: {key}"] = util_tags.get_value(i, key)

                instances.append(inst)

    return sorted(instances, key=lambda i: str(i["Name"]))


def volume_tags(
    config: Config, name: Optional[str] = None, name_match: Optional[str] = None, keys: Sequence[str] = []
) -> List[Dict[str, Any]]:
    """List EC2 volumes with their tags."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_volumes(Filters=name_filters(name, name_match))

    volumes: List[Dict[str, Any]] = []
    for v in response["Volumes"]:
        vol = {"VolumeId": v["VolumeId"], "Name": util_tags.get_value(v, "Name")}
        if not keys:
            vol["Tags"] = ", ".join(f"{tag['Key']}={tag['Value']}" for tag in v.get("Tags", []))
        else:
            for key in keys:
                vol[f"Tag: {key}"] = util_tags.get_value(v, key)

        volumes.append(vol)

    return sorted(volumes, key=lambda i: str(i["Name"]))


def start(config: Config, name: str) -> List[Instance]:
    """Start EC2 instance."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    print(f"Starting instances with the name {name} ... ")

    if not name:
        # avoid starting all instances when there's no name
        raise NoInstancesError(name=name)

    instances = describe(config, name)

    if not instances:
        raise NoInstancesError(name=name)

    instance_ids = [instance["InstanceId"] for instance in instances]
    ec2_client.start_instances(InstanceIds=instance_ids)

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=instance_ids)

    return describe(config, name)


def stop(config: Config, name: str) -> List[Dict[str, Any]]:
    """Stop EC2 instance."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    if not name:
        # avoid stopping all instances when there's no name
        raise NoInstancesError(name=name)

    instances = describe(config, name)

    if not instances:
        raise NoInstancesError(name=name)

    response = ec2_client.stop_instances(InstanceIds=[instance["InstanceId"] for instance in instances])

    return [{"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["StoppingInstances"]]


def terminate(config: Config, name: str) -> List[Dict[str, Any]]:
    """Terminate EC2 instance."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    if not name:
        # avoid terminating all instances when there's no name
        raise NoInstancesError(name=name)

    instances = describe(config, name)

    if not instances:
        raise NoInstancesError(name=name)

    response = ec2_client.terminate_instances(InstanceIds=[instance["InstanceId"] for instance in instances])

    return [
        {"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["TerminatingInstances"]
    ]


def modify(config: Config, name: str, type: str) -> List[Instance]:
    """Change an instance's type."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    if not name:
        # avoid modifying all instances when there's no name
        raise NoInstancesError(name=name)

    instances = describe(config, name)

    if not instances:
        raise NoInstancesError(name=name)

    instance_id = instances[0]["InstanceId"]
    ec2_client.modify_instance_attribute(InstanceId=instance_id, InstanceType={"Value": type})
    ec2_client.modify_instance_attribute(InstanceId=instance_id, EbsOptimized={"Value": is_ebs_optimizable(type)})

    return describe(config, name)


def create_key_pair(config: Config, key_name: str, file_path: str) -> str:
    """Create a key pair."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    path = os.path.expanduser(file_path)
    with open(path, "x") as file:
        key = ec2_client.create_key_pair(KeyName=key_name)
        file.write(key["KeyMaterial"])
        os.chmod(path, 0o600)

    return f"Created key pair {key_name} and saved private key to {path}"


def logs(config: Config, name: str) -> str:
    """Show the system logs."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    if not name:
        # avoid describing all instances when there's no name
        raise NoInstancesError(name=name)

    instances = describe(config, name)

    if not instances:
        raise NoInstancesError(name=name)

    instance_id = instances[0]["InstanceId"]
    response = ec2_client.get_console_output(InstanceId=instance_id)

    return response.get("Output", "No logs yet 😔")


def templates(config: Config) -> List[Dict[str, Any]]:
    """Describe launch templates."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_launch_templates()

    return [
        {"Name": t["LaunchTemplateName"], "Default Version": t["DefaultVersionNumber"]}
        for t in response["LaunchTemplates"]
    ]


def status(
    config: Config,
    name: Optional[str] = None,
    name_match: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Describe instances status checks."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    kwargs: Dict[str, Any] = {"MaxResults": 1000}

    response_fut = executor.submit(ec2_client.describe_instance_status, **kwargs)
    instances = executor.submit(describe_running_instances_names, config).result()
    response = response_fut.result()

    def match(instance_id: str, instance_name: Optional[str]) -> bool:
        # describe_instance_status doesn't support name filters in the request so match here
        if not name and not name_match:
            return True

        if name is not None:
            return (name.startswith("i-") and name == instance_id) or (name == instance_name)

        return not name_match or name_match in (instance_name or "")

    statuses = []
    while True:
        statuses.extend(
            [
                {
                    "InstanceId": i["InstanceId"],
                    "State": i["InstanceState"]["Name"],
                    "Name": instances.get(i["InstanceId"], None),
                    "System status check": status_text(i["SystemStatus"]),
                    "Instance status check": status_text(i["InstanceStatus"]),
                }
                for i in response["InstanceStatuses"]
                if match(i["InstanceId"], instances.get(i["InstanceId"], None))
            ]
        )

        next_token = response.get("NextToken", None)
        if next_token:
            kwargs["NextToken"] = next_token
            response = ec2_client.describe_instance_status(**kwargs)
        else:
            break

    return sorted(
        statuses,
        key=lambda i: "".join(str(i[field]) for field in ["State", "Name"]),
    )


def status_text(summary: InstanceStatusSummaryTypeDef, key: str = "reachability") -> str:
    status = [d for d in summary["Details"] if d["Name"] == key][0]
    return f"{status['Name']} {status['Status']}" + (
        f" since {status['ImpairedSince']}" if status.get("ImpairedSince", None) else ""
    )


def user_data(config: Config, name: str) -> Optional[str]:
    """Describe user data for an instance."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    if not name:
        # avoid describing all instances when there's no name
        raise NoInstancesError(name=name)

    instances = describe(config, name)

    if not instances:
        raise NoInstancesError(name=name)

    instance_id = instances[0]["InstanceId"]
    response = ec2_client.describe_instance_attribute(Attribute="userData", InstanceId=instance_id)

    try:
        return base64.b64decode(response["UserData"]["Value"]).decode("utf-8")
    except KeyError:
        return None


def name_filters(name_or_id: Optional[str] = None, name_match: Optional[str] = None) -> List[FilterTypeDef]:
    if name_or_id and name_or_id.startswith("i-"):
        return [{"Name": "instance-id", "Values": [name_or_id]}]
    elif name_or_id:
        return [{"Name": "tag:Name", "Values": [name_or_id]}]
    elif name_match:
        return [{"Name": "tag:Name", "Values": [f"*{name_match}*"]}]
    else:
        return []


def read_file(filepath: str) -> str:
    with open(os.path.expanduser(filepath)) as file:
        return file.read()


def read_url(url: str) -> str:
    import requests

    r = requests.get(url)
    r.raise_for_status()
    return r.text
