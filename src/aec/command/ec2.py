from __future__ import annotations

import base64
import os
import os.path
from collections import defaultdict
from collections.abc import Sequence
from time import sleep
from typing import TYPE_CHECKING, Any, cast

import boto3
from typing_extensions import TypedDict

from aec.util.ec2_util import describe_running_instances_names
from aec.util.errors import NoInstancesError
from aec.util.threads import executor

if TYPE_CHECKING:
    from mypy_boto3_ec2.literals import InstanceTypeType
    from mypy_boto3_ec2.type_defs import (
        BlockDeviceMappingTypeDef,
        DescribeVolumesResultTypeDef,
        FilterTypeDef,
        InstanceStatusSummaryTypeDef,
        TagSpecificationTypeDef,
        TagTypeDef,
    )

import aec.command.ami as ami_cmd
import aec.util.tags as util_tags
from aec.util.config import Config
from aec.util.ec2_types import RunArgs


def is_ebs_optimizable(instance_type: str) -> bool:
    return not instance_type.startswith("t2")


Instance = TypedDict(
    "Instance",
    {
        "InstanceId": "str",
        "State": "str",
        "Name": "str | None",
        "Type": "str",
        "DnsName": "str",
        "SubnetId": "str",
        "Volumes": "list[str]",
        "Image.CreationDate": "str",
    },
    total=False,
)


def launch(
    config: Config,
    name: str,
    ami: str | None = None,
    template: str | None = None,
    volume_size: int | None = None,
    encrypted: bool = True,
    instance_type: str | None = None,
    key_name: str | None = None,
    userdata: str | None = None,
    wait_ssm: bool = False,
) -> list[Instance]:
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

    tags: list[TagTypeDef] = [{"Key": "Name", "Value": name}]
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

    # use IMDSv2 to prevent SSRF and enable instance metadata tags
    runargs["MetadataOptions"] = {"HttpTokens": "required", "InstanceMetadataTags": "enabled"}

    region_name = ec2_client.meta.region_name

    print(
        f"Launching {'a ' + instance_type if instance_type else 'an instance'} in "
        + f"{region_name}{vpc_name} named {name} using {desc} ... "
    )
    response = ec2_client.run_instances(**runargs)

    instance_id = response["Instances"][0]["InstanceId"]

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])

    if wait_ssm:
        print(f"Instance {instance_id} running. Waiting for SSM agent to come online ...")
        _wait_ssm_agent_online(config, [instance_id])

    # the response from run_instances above always contains an empty string
    # for PublicDnsName, so we call describe to get it
    return describe(config=config, idents=instance_id)


def _wait_ssm_agent_online(config: Config, instance_ids: list[str]) -> None:
    """
    Wait for ssm to come online.

    This ensures the instance is ready to accept ssh logins.
    """
    #
    client = boto3.client("ssm", region_name=config.get("region", None))

    timeout = 60 * 3  # seconds
    for _ in range(timeout):
        response = client.describe_instance_information(Filters=[{"Key": "InstanceIds", "Values": instance_ids}])
        if response["InstanceInformationList"]:
            return
        sleep(1)

    raise TimeoutError(f"SSM agent not online after {timeout} seconds")


def describe(
    config: Config,
    idents: str | list[str] | None = None,
    name_match: str | None = None,
    include_terminated: bool = False,
    show_running_only: bool = False,
    sort_by: str = "State,Name",
    columns: str = "InstanceId,State,Name,Type,DnsName,LaunchTime,ImageId",
) -> list[Instance]:
    """List EC2 instances in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    filters = to_filters(idents, name_match)
    if show_running_only:
        filters.append({"Name": "instance-state-name", "Values": ["pending", "running"]})

    kwargs: dict[str, Any] = {"MaxResults": 1000, "Filters": filters}

    response_fut = executor.submit(ec2_client.describe_instances, **kwargs)

    cols = columns.split(",")

    # don't sort by cols we aren't showing
    sort_cols = [sc for sc in sort_by.split(",") if sc in cols]

    if "Volumes" in columns:
        # fetch volume info
        volumes_response: DescribeVolumesResultTypeDef = executor.submit(ec2_client.describe_volumes).result()
        volumes: dict[str, list[str]] = defaultdict(list)
        for v in volumes_response["Volumes"]:
            for a in v["Attachments"]:
                volumes[a["InstanceId"]].append(f"Size={v['Size']} GiB")
    else:
        volumes = {}

    response = response_fut.result()

    # import json; print(json.dumps(response))

    instances: list[Instance] = []
    while True:
        if "Image." in columns:
            # fetch image info
            images_ids = [i["ImageId"] for r in response["Reservations"] for i in r["Instances"]]
            images_response = ec2_client.describe_images(ImageIds=images_ids)
            images_by_id = {i["ImageId"]: i for i in images_response["Images"]}
        else:
            images_by_id = {}

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
                            desc[col] = i["PublicDnsName"] or i["PrivateDnsName"]
                        elif col == "Volumes":
                            desc[col] = volumes.get(i["InstanceId"], [])
                        elif "Image." in col:
                            key = col.split(".")[1]
                            desc[col] = images_by_id[i["ImageId"]].get(key, None)
                        else:
                            desc[col] = i.get(col, None)

                    instances.append(desc)

        next_token = response.get("NextToken", None)
        if next_token:
            kwargs["NextToken"] = next_token
            response = ec2_client.describe_instances(**kwargs)
        else:
            break

    return sorted(
        instances,
        key=lambda i: "".join(str(i[field]) for field in sort_cols),
    )


def describe_tags(
    config: Config,
    ident: str | None = None,
    name_match: str | None = None,
    keys: Sequence[str] = [],
    volumes: bool = False,
) -> list[dict[str, Any]]:
    """List EC2 instances or volumes with their tags."""
    if volumes:
        return volume_tags(config, ident, name_match, keys)

    return instance_tags(config, ident, name_match, keys)


def rename(
    config: Config,
    ident: str,
    new_name: str,
) -> list[Instance]:
    """Rename EC2 instance(s)."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, ident, include_terminated=True)

    ids = [i["InstanceId"] for i in instances]

    if not ids:
        raise NoInstancesError(name=ident)

    ec2_client.create_tags(Resources=ids, Tags=[{"Key": "Name", "Value": new_name}])

    return describe(config, new_name, include_terminated=True)


def tag(
    config: Config,
    ident: str | None = None,
    name_match: str | None = None,
    tags: Sequence[str] = [],
) -> list[dict[str, Any]]:
    """Tag EC2 instance(s)."""
    if not ident and not name_match:
        # avoid tagging all instances when there's no name
        raise ValueError("Missing instance identifier or name_match")

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    tagdefs: list[TagTypeDef] = []

    for t in tags:
        parts = t.split("=")
        tagdefs.append({"Key": parts[0], "Value": parts[1]})

    instances = describe(config, ident, name_match)

    ids = [i["InstanceId"] for i in instances]

    if not ids:
        raise NoInstancesError(name=ident, name_match=name_match)

    ec2_client.create_tags(Resources=ids, Tags=tagdefs)

    return describe_tags(config, ident, name_match, keys=[d["Key"] for d in tagdefs])


def instance_tags(
    config: Config, ident: str | None = None, name_match: str | None = None, keys: Sequence[str] = []
) -> list[dict[str, Any]]:
    """List EC2 instances with their tags."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances(Filters=to_filters(ident, name_match))

    instances: list[dict[str, Any]] = []
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
    config: Config, ident: str | None = None, name_match: str | None = None, keys: Sequence[str] = []
) -> list[dict[str, Any]]:
    """List EC2 volumes with their tags."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_volumes(Filters=to_filters(ident, name_match))

    volumes: list[dict[str, Any]] = []
    for v in response["Volumes"]:
        vol = {"VolumeId": v["VolumeId"], "Name": util_tags.get_value(v, "Name")}
        if not keys:
            vol["Tags"] = ", ".join(f"{tag['Key']}={tag['Value']}" for tag in v.get("Tags", []))
        else:
            for key in keys:
                vol[f"Tag: {key}"] = util_tags.get_value(v, key)

        volumes.append(vol)

    return sorted(volumes, key=lambda i: str(i["Name"]))


def start(
    config: Config,
    idents: str | list[str],
    wait_ssm: bool = False,
) -> list[Instance]:
    """Start EC2 instance(s)."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, idents)

    if not instances:
        raise NoInstancesError(idents)

    for i in instances:
        name_or_id = i.get("Name") or i["InstanceId"]
        print(f"Starting instance {name_or_id} ... ")

    instance_ids = [instance["InstanceId"] for instance in instances]

    ec2_client.start_instances(InstanceIds=instance_ids)

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=instance_ids)

    if wait_ssm:
        instances_text = "Instances" if len(instance_ids) > 1 else "Instance"
        print(f"{instances_text} running. Waiting for SSM agent to come online ...")
        _wait_ssm_agent_online(config, instance_ids)

    return describe(config, idents)


def stop(config: Config, idents: list[str]) -> list[dict[str, Any]]:
    """Stop EC2 instance(s)."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, idents)

    if not instances:
        raise NoInstancesError(name=idents)

    instance_ids = [instance["InstanceId"] for instance in instances]
    response = ec2_client.stop_instances(InstanceIds=instance_ids)

    return [{"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["StoppingInstances"]]


def terminate(config: Config, idents: list[str], yes: bool = True) -> list[dict[str, Any]]:
    """Terminate EC2 instance(s)."""

    if not idents or not idents[0]:
        # avoid terminating all instances when there's no identifier
        # we already check args via arg parser, so this is defence in depth
        raise ValueError("Missing instance identifier")

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, idents)

    if not instances:
        raise NoInstancesError(name=idents)

    print("The following instances will be terminated:")
    for instance in instances:
        name = instance.get("Name")
        instance_id = instance["InstanceId"]
        if name:
            print(f"- {name} ({instance_id})")
        else:
            print(f"- {instance_id}")

    if not yes:
        confirm = input("Are you sure you want to terminate these instances? (y/n): ")
        if confirm.lower() != "y":
            print("Termination cancelled.")
            return []

    instance_ids = [instance["InstanceId"] for instance in instances]
    response = ec2_client.terminate_instances(InstanceIds=instance_ids)

    return [
        {"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["TerminatingInstances"]
    ]


def modify(config: Config, ident: str, type: str) -> list[Instance]:
    """Change an instance's type."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, ident)

    if not instances:
        raise NoInstancesError(name=ident)

    instance_id = instances[0]["InstanceId"]
    ec2_client.modify_instance_attribute(InstanceId=instance_id, InstanceType={"Value": type})
    ec2_client.modify_instance_attribute(InstanceId=instance_id, EbsOptimized={"Value": is_ebs_optimizable(type)})

    return describe(config, ident)


def restart(config: Config, ident: str, type: str | None = None, wait_ssm: bool = False) -> list[Instance]:
    """Restart EC2 instance, optionally changing the instance type."""
    print(f"Stopping instance {ident}")
    stop(config, [ident])

    instance_status = describe(config, ident)[0]["State"]
    while instance_status != "stopped":
        print(f"Waiting for instance {ident} to stop ...")
        sleep(5)
        instance_status = describe(config, ident)[0]["State"]

    if type:
        print(f"Changing instance type to {type}")
        modify(config, ident, type)

    return start(config, ident, wait_ssm=wait_ssm)


def create_key_pair(config: Config, key_name: str, file_path: str) -> str:
    """Create a key pair."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    path = os.path.expanduser(file_path)
    with open(path, "x") as file:
        key = ec2_client.create_key_pair(KeyName=key_name)
        file.write(key["KeyMaterial"])
        os.chmod(path, 0o600)

    return f"Created key pair {key_name} and saved private key to {path}"


def logs(config: Config, ident: str) -> str:
    """Show the system logs."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, ident)

    if not instances:
        raise NoInstancesError(name=ident)

    instance_id = instances[0]["InstanceId"]
    response = ec2_client.get_console_output(InstanceId=instance_id)

    return response.get("Output", "No logs yet 😔")


def templates(config: Config) -> list[dict[str, Any]]:
    """Describe launch templates."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_launch_templates()

    return [
        {"Name": t["LaunchTemplateName"], "Default Version": t["DefaultVersionNumber"]}
        for t in response["LaunchTemplates"]
    ]


def status(
    config: Config,
    ident: str | None = None,
    name_match: str | None = None,
) -> list[dict[str, Any]]:
    """Describe instances status checks."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    kwargs: dict[str, Any] = {"MaxResults": 1000}

    response_fut = executor.submit(ec2_client.describe_instance_status, **kwargs)
    instances = executor.submit(describe_running_instances_names, config).result()
    response = response_fut.result()

    def match(instance_id: str, instance_name: str | None) -> bool:
        # describe_instance_status doesn't support name filters in the request so match here
        if not ident and not name_match:
            return True

        if ident is not None:
            return (ident.startswith("i-") and ident == instance_id) or (ident == instance_name)

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
    status = next(d for d in summary["Details"] if d["Name"] == key)
    return f"{status['Name']} {status['Status']}" + (
        f" since {status['ImpairedSince']}" if status.get("ImpairedSince", None) else ""
    )


def sec_groups(config: Config, vpc_id: str | None = None) -> list[dict[str, str | None]]:
    """
    Describe security groups in the region, optionally filtered by VPC ID.
    """

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    # Prepare filters
    filters: list[FilterTypeDef] = []
    if vpc_id:
        filters.append({"Name": "vpc-id", "Values": [vpc_id]})

    paginator = ec2_client.get_paginator("describe_security_groups")
    pages = paginator.paginate(Filters=filters)

    groups_info: list[dict[str, str | None]] = []

    for page in pages:
        groups_info.extend(
            {
                "GroupId": sg["GroupId"],
                "GroupName": sg.get("GroupName"),
                "Description": sg.get("Description"),
                "VpcId": sg.get("VpcId"),
            }
            for sg in page["SecurityGroups"]
        )

    # Sort the results, e.g., by VpcId then GroupName
    return sorted(groups_info, key=lambda g: (g["VpcId"], g["GroupName"]))


def subnets(config: Config, vpc_id: str | None = None) -> list[dict[str, Any]]:
    """Describe subnets."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}] if vpc_id else [])

    return sorted(
        [
            {
                "SubnetId": subnet["SubnetId"],
                "VpcId": subnet["VpcId"],
                "AvailabilityZone": subnet["AvailabilityZone"],
                "CidrBlock": subnet["CidrBlock"],
                "Name": util_tags.get_value(subnet, "Name"),
            }
            for subnet in response["Subnets"]
        ],
        key=lambda s: s["VpcId"] + s["AvailabilityZone"] + (s["Name"] or ""),
    )


def user_data(config: Config, ident: str) -> str | None:
    """Describe user data for an instance."""
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, ident)

    if not instances:
        raise NoInstancesError(name=ident)

    instance_id = instances[0]["InstanceId"]
    response = ec2_client.describe_instance_attribute(Attribute="userData", InstanceId=instance_id)

    try:
        return base64.b64decode(response["UserData"]["Value"]).decode("utf-8")
    except KeyError:
        return None


def to_filters(idents: str | list[str] | None = None, name_match: str | None = None) -> list[FilterTypeDef]:
    if not idents:
        if name_match:
            return [{"Name": "tag:Name", "Values": [f"*{name_match}*"]}]
        else:
            return []

    if isinstance(idents, str):
        idents = [idents]

    # Separate instance IDs and names
    ids = []
    names = []

    for id_or_name in idents:
        if id_or_name.startswith("i-"):
            ids.append(id_or_name)
        else:
            names.append(id_or_name)

    filters = []

    if ids and names:
        raise ValueError("Cannot specify both instance IDs and names, only one or the other")

    if ids:
        filters.append({"Name": "instance-id", "Values": ids})

    if names:
        filters.append({"Name": "tag:Name", "Values": names})

    return filters


def read_file(filepath: str) -> str:
    with open(os.path.expanduser(filepath)) as file:
        return file.read()


def read_url(url: str) -> str:
    import requests

    r = requests.get(url, timeout=5)
    r.raise_for_status()
    return r.text
