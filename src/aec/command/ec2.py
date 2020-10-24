import os
import os.path
from typing import Any, AnyStr, Dict, List, NamedTuple, Optional

import boto3
from mypy_boto3_ec2.type_defs import FilterTypeDef
from typing_extensions import TypedDict

from aec.util.list import first_or_else


def delete_image(config: Dict[str, Any], ami: str) -> None:
    """Deregister an AMI and delete its snapshot."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = describe_images(config, ami, show_snapshot_id=True)

    ec2_client.deregister_image(ImageId=ami)

    ec2_client.delete_snapshot(SnapshotId=response[0]["SnapshotId"])


def share_image(config: Dict[str, Any], ami: str, account: str) -> None:
    """Share an AMI with another account."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    ec2_client.modify_image_attribute(
        ImageId=ami,
        LaunchPermission={"Add": [{"UserId": account}]},
        OperationType="add",
        UserIds=[account],
        Value="string",
        DryRun=False,
    )


Image = TypedDict(
    "Image",
    {"Name": Optional[str], "ImageId": str, "CreationDate": str, "RootDeviceName": str, "SnapshotId": str},
    total=False,
)


def describe_images(
    config: Dict[str, Any],
    ami: Optional[str] = None,
    owner: Optional[str] = None,
    name_match: Optional[str] = None,
    show_snapshot_id: bool = False,
) -> List[Image]:
    """List AMIs."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    if ami:
        response = ec2_client.describe_images(ImageIds=[ami])
    else:
        if owner:
            owners_filter = [owner]
        else:
            describe_images_owners = config.get("describe_images_owners", None)

            if not describe_images_owners:
                owners_filter = ["self"]
            elif isinstance(describe_images_owners, str):
                owners_filter = [describe_images_owners]
            else:
                owners_filter: List[str] = describe_images_owners

        if name_match is None:
            name_match = config.get("describe_images_name_match", None)

        filters: List[FilterTypeDef] = [] if name_match is None else [{"Name": "name", "Values": [f"*{name_match}*"]}]

        print(
            f"Describing images owned by {owners_filter} with name matching {name_match if name_match else '*'}"
        )
        response = ec2_client.describe_images(Owners=owners_filter, Filters=filters)

    images: List[Image] = [
        {
            "Name": i.get("Name", None),
            "ImageId": i["ImageId"],
            "CreationDate": i["CreationDate"],
            "RootDeviceName": i["RootDeviceName"],
        }
        for i in response["Images"]
    ]

    images = []
    for i in response["Images"]:
        image: Image = {
            "Name": i.get("Name", None),
            "ImageId": i["ImageId"],
            "CreationDate": i["CreationDate"],
            "RootDeviceName": i["RootDeviceName"],
        }
        if show_snapshot_id:
            image["SnapshotId"] = i["BlockDeviceMappings"][0]["Ebs"]["SnapshotId"]
        images.append(image)

    return sorted(images, key=lambda i: i["CreationDate"], reverse=True)


class AmiMatcher(NamedTuple):
    owner: str
    match_string: str


amazon_base_account_id = "137112412989"
canonical_account_id = "099720109477"

ami_keywords = {
    "amazon2": AmiMatcher(amazon_base_account_id, "amzn2-ami-hvm*x86_64-gp2"),
    "ubuntu1604": AmiMatcher(canonical_account_id, "ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64"),
    "ubuntu1804": AmiMatcher(canonical_account_id, "ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64"),
    "ubuntu2004": AmiMatcher(canonical_account_id, "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64"),
}


def launch(
    config: Dict[str, Any],
    name: str,
    ami: str,
    volume_size: int = 100,
    encrypted: bool = True,
    instance_type: str = "t2.medium",
    key_name: Optional[str] = None,
    userdata: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Launch a tagged EC2 instance with an EBS volume.

    Specify an AMI keyword to select the latest AMI for that distro and version.
    """

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    additional_tags = config["additional_tags"] if config.get("additional_tags", None) else {}
    tags = [{"Key": "Name", "Value": name}] + [{"Key": k, "Value": v} for k, v in additional_tags.items()]
    kms_key_id = config.get("kms_key_id", None)
    security_group = config["vpc"]["security_group"]

    if not key_name:
        key_name = config["key_name"]

    image = fetch_image(config, ami)

    # TODO: support multiple subnets
    kwargs: Dict[str, Any] = {
        "ImageId": image["ImageId"],
        "MaxCount": 1,
        "MinCount": 1,
        "KeyName": key_name,
        "InstanceType": instance_type,
        "TagSpecifications": [{"ResourceType": "instance", "Tags": tags}, {"ResourceType": "volume", "Tags": tags}],
        "EbsOptimized": False if instance_type.startswith("t2") else True,
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

    print(f"Launching a {instance_type} in {region_name} named {name} in " f"vpc {config['vpc']['name']}... ")
    response = ec2_client.run_instances(**kwargs)

    instance = response["Instances"][0]

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance["InstanceId"]])

    # TODO: wait until instance checks passed (as they do in the console)

    # the response from run_instances above always contains an empty string
    # for PublicDnsName, so we call describe to get it
    return describe(config=config, name=name)


def fetch_image(config: Dict[str, Any], ami: str) -> Image:
    ami_matcher = ami_keywords.get(ami, None)
    if ami_matcher:
        try:
            # lookup the latest ami by name match
            ami_details = describe_images(config, owner=ami_matcher.owner, name_match=ami_matcher.match_string)[0]
        except IndexError:
            raise RuntimeError(
                f"Could not find ami with name matching {ami_matcher.match_string} owned by account {ami_matcher.owner}"
            )
    else:
        try:
            # lookup by ami id
            ami_details = describe_images(config, ami=ami)[0]
        except IndexError:
            raise RuntimeError(f"Could not find {ami}")
    return ami_details


def describe(
    config: Dict[str, Any],
    name: Optional[str] = None,
    name_match: Optional[str] = None,
    include_terminated: bool = False,
) -> List[Dict[str, Any]]:
    """List EC2 instances in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    filters: List[FilterTypeDef] = []
    if name:
        filters = [{"Name": "tag:Name", "Values": [name]}]
    elif name_match:
        filters = [{"Name": "tag:Name", "Values": [f"*{name_match}*"]}]

    response = ec2_client.describe_instances(Filters=filters)

    # print(response["Reservations"][0]["Instances"][0])

    instances: List[Dict[str, Any]] = [
        {
            "State": i["State"]["Name"],
            "Name": first_or_else([t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"], None),
            "Type": i["InstanceType"],
            "DnsName": i["PublicDnsName"] if i.get("PublicDnsName", None) != "" else i["PrivateDnsName"],
            "LaunchTime": i["LaunchTime"],
            "ImageId": i["ImageId"],
            "InstanceId": i["InstanceId"],
        }
        for r in response["Reservations"]
        for i in r["Instances"]
        if include_terminated or i["State"]["Name"] != "terminated"
    ]

    return sorted(instances, key=lambda i: i["State"] + str(i["Name"]))


def start(config: Dict[str, Any], name: str) -> List[Dict[str, Any]]:
    """Start EC2 instances by name."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    print(f"Starting instances with the name {name} ... ")

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances named {name}")

    instance_ids = [instance["InstanceId"] for instance in instances]
    ec2_client.start_instances(InstanceIds=instance_ids)

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=instance_ids)

    return describe(config, name)


def stop(config: Dict[str, Any], name: str) -> List[Dict[str, Any]]:
    """Stop EC2 instances by name."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances named {name}")

    response = ec2_client.stop_instances(InstanceIds=[instance["InstanceId"] for instance in instances])

    return [{"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["StoppingInstances"]]


def terminate(config: Dict[str, Any], name: str) -> List[Dict[str, Any]]:
    """Terminate EC2 instances by name."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances named {name}")

    response = ec2_client.terminate_instances(InstanceIds=[instance["InstanceId"] for instance in instances])

    return [
        {"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["TerminatingInstances"]
    ]


def modify(config: Dict[str, Any], name: str, type: str) -> List[Dict[str, Any]]:
    """Change an instance's type."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances named {name}")

    instance_id = instances[0]["InstanceId"]
    ec2_client.modify_instance_attribute(InstanceId=instance_id, InstanceType={"Value": type})

    return describe(config, name)


def logs(config: Dict[str, Any], name: str) -> str:
    """Show the system logs."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    instances = describe(config, name)

    if not instances:
        raise Exception(f"No instances named {name}")

    instance_id = instances[0]["InstanceId"]
    response = ec2_client.get_console_output(InstanceId=instance_id)

    return response["Output"]


def read_file(filepath: str) -> AnyStr:
    with open(os.path.expanduser(filepath)) as file:
        return file.read()
