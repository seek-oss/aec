import os
import os.path
from typing import Any, Dict, List, Optional

import boto3
from mypy_boto3_ec2.type_defs import FilterTypeDef

import aec.command.ami as ami_cmd
import aec.util.instance as instance
from aec.util.config import Config


def is_ebs_optimizable(instance_type: str) -> bool:
    return not instance_type.startswith("t2")


def launch(
    config: Config,
    name: str,
    ami: str,
    volume_size: int = 100,
    encrypted: bool = True,
    instance_type: str = "t2.medium",
    key_name: Optional[str] = None,
    userdata: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Launch a tagged EC2 instance with an EBS volume."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    additional_tags = config.get("additional_tags", {})
    tags = [{"Key": "Name", "Value": name}] + [{"Key": k, "Value": v} for k, v in additional_tags.items()]
    kms_key_id = config.get("kms_key_id", None)
    security_group = config["vpc"]["security_group"]

    if not key_name:
        key_name = config["key_name"]

    image = ami_cmd.fetch(config, ami)

    # TODO: support multiple subnets
    kwargs: Dict[str, Any] = {
        "ImageId": image["ImageId"],
        "MaxCount": 1,
        "MinCount": 1,
        "KeyName": key_name,
        "InstanceType": instance_type,
        "TagSpecifications": [{"ResourceType": "instance", "Tags": tags}, {"ResourceType": "volume", "Tags": tags}],
        "EbsOptimized": is_ebs_optimizable(instance_type),
        "NetworkInterfaces": [
            {
                "DeviceIndex": 0,
                "Description": "Primary network interface",
                "DeleteOnTermination": True,
                "SubnetId": config["vpc"]["subnet"],
                "Ipv6AddressCount": 0,
                "Groups": security_group if isinstance(security_group, list) else [security_group],
            }
        ],
        "BlockDeviceMappings": [
            {
                "DeviceName": image["RootDeviceName"],
                "Ebs": {
                    "VolumeSize": volume_size,
                    "DeleteOnTermination": True,
                    "VolumeType": "gp2",
                    "Encrypted": encrypted,
                },
            }
        ],
    }

    associate_public_ip_address = config["vpc"].get("associate_public_ip_address", None)
    if associate_public_ip_address is not None:
        kwargs["NetworkInterfaces"][0]["AssociatePublicIpAddress"] = associate_public_ip_address

    iam_instance_profile_arn = config.get("iam_instance_profile_arn", None)
    if iam_instance_profile_arn:
        kwargs["IamInstanceProfile"] = {"Arn": iam_instance_profile_arn}

    if kms_key_id is not None:
        kwargs["BlockDeviceMappings"][0]["Ebs"]["KmsKeyId"] = kms_key_id

    if userdata:
        kwargs["UserData"] = read_file(userdata)

    region_name = ec2_client.meta.region_name

    print(
        f"Launching a {instance_type} in {region_name} vpc {config['vpc']['name']} named {name} using {image['Name']} ... "
    )
    response = ec2_client.run_instances(**kwargs)

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
) -> List[Dict[str, Any]]:
    """List EC2 instances in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    filters: List[FilterTypeDef] = []
    if name and name.startswith("i-"):
        filters = [{"Name": "instance-id", "Values": [name]}]
    elif name:
        filters = [{"Name": "tag:Name", "Values": [name]}]
    elif name_match:
        filters = [{"Name": "tag:Name", "Values": [f"*{name_match}*"]}]

    response = ec2_client.describe_instances(Filters=filters)

    # print(response["Reservations"][0]["Instances"][0])

    instances: List[Dict[str, Any]] = [
        {
            "State": i["State"]["Name"],
            "Name": instance.tag(i, "Name"),
            "Type": i["InstanceType"],
            "DnsName": i["PublicDnsName"] if i.get("PublicDnsName", None) != "" else i["PrivateDnsName"],
            "LaunchTime": i["LaunchTime"],
            "ImageId": i["ImageId"],
            "InstanceId": i["InstanceId"],
        }
        for r in response["Reservations"]
        for i in r["Instances"]
        if (include_terminated or i["State"]["Name"] != "terminated")
        and (not show_running_only or i["State"]["Name"] in ["pending", "running"])
    ]

    return sorted(instances, key=lambda i: i["State"] + str(i["Name"]))


def tags(config: Config, keys: List[str] = []) -> List[Dict[str, Any]]:
    """List EC2 instances with their tags."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances()

    instances: List[Dict[str, Any]] = []
    for r in response["Reservations"]:
        for i in r["Instances"]:
            if i["State"]["Name"] != "terminated":
                inst = {"InstanceId": i["InstanceId"], "Name": instance.tag(i, "Name")}
                if not keys:
                    inst["Tags"] = ", ".join(f"{tag['Key']}={tag['Value']}" for tag in i["Tags"])
                else:
                    for key in keys:
                        inst[f"Tag: {key}"] = instance.tag(i, key)

                instances.append(inst)

    return sorted(instances, key=lambda i: str(i["Name"]))


def start(config: Config, name: str) -> List[Dict[str, Any]]:
    """Start EC2 instance."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    print(f"Starting instances with the name {name} ... ")

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances with {pretty_name_or_id(name)}")

    instance_ids = [instance["InstanceId"] for instance in instances]
    ec2_client.start_instances(InstanceIds=instance_ids)

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=instance_ids)

    return describe(config, name)


def stop(config: Config, name: str) -> List[Dict[str, Any]]:
    """Stop EC2 instance."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances with {pretty_name_or_id(name)}")

    response = ec2_client.stop_instances(InstanceIds=[instance["InstanceId"] for instance in instances])

    return [{"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["StoppingInstances"]]


def pretty_name_or_id(name: str) -> str:
    return f"instance id {name}" if name.startswith("i-") else f"name {name}"


def terminate(config: Config, name: str) -> List[Dict[str, Any]]:
    """Terminate EC2 instance."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances with {pretty_name_or_id(name)}")

    response = ec2_client.terminate_instances(InstanceIds=[instance["InstanceId"] for instance in instances])

    return [
        {"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["TerminatingInstances"]
    ]


def modify(config: Config, name: str, type: str) -> List[Dict[str, Any]]:
    """Change an instance's type."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances with {pretty_name_or_id(name)}")

    instance_id = instances[0]["InstanceId"]
    ec2_client.modify_instance_attribute(InstanceId=instance_id, InstanceType={"Value": type})
    ec2_client.modify_instance_attribute(InstanceId=instance_id, EbsOptimized={"Value": is_ebs_optimizable(type)})

    return describe(config, name)


def logs(config: Config, name: str) -> str:
    """Show the system logs."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances with {pretty_name_or_id(name)}")

    instance_id = instances[0]["InstanceId"]
    response = ec2_client.get_console_output(InstanceId=instance_id)

    return response["Output"]


def read_file(filepath: str) -> str:
    with open(os.path.expanduser(filepath)) as file:
        return file.read()
