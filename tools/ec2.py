import os.path
from enum import Enum
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Optional

import boto3
import typer
from argh import arg

from tools.cli import Cli, ProfileOption, Typer

cli = Cli(config_file="~/.aec/ec2.toml").cli

app = Typer()
profile_option = ProfileOption("~/.aec/ec2.toml")

@arg("ami", help="ami id")
@cli
def delete_image(config, ami: str):
    """
    Deregister an AMI and deletes its snapshot
    """
    ec2_client = boto3.client("ec2", region_name=config["region"])

    response = describe_images(config, ami)

    ec2_client.deregister_image

    ec2_client.deregister_image(ImageId=ami)

    ec2_client.delete_snapshot(SnapshotId=response[0]["SnapshotId"])


@arg("ami", help="ami id")
@arg("account", help="account id")
@cli
def share_image(config, ami: str, account: str):
    """
    Share an AMI with another account
    """

    ec2_client = boto3.client("ec2", region_name=config["region"])

    ec2_client.modify_image_attribute(
        ImageId=ami,
        LaunchPermission={"Add": [{"UserId": account}]},
        OperationType="add",
        UserIds=[account],
        Value="string",
        DryRun=False,
    )


@arg("--ami", help="filter to this ami id", default=None)
@cli
def describe_images(config, ami) -> List[Dict[str, Any]]:
    """
    List AMIs
    """

    ec2_client = boto3.client("ec2", region_name=config["region"])

    owners = config["describe_images_owners"] if config.get("describe_images_owners", None) else "self"

    if isinstance(owners, str):
        owners = [owners]

    if ami:
        response = ec2_client.describe_images(ImageIds=[ami])
    else:
        response = ec2_client.describe_images(Owners=owners)

    images = [
        {
            "ImageId": i["ImageId"],
            "Name": i.get("Name", None),
            "Description": i.get("Description", None),
            "CreationDate": i["CreationDate"],
            "SnapshotId": i["BlockDeviceMappings"][0]["Ebs"]["SnapshotId"],
        }
        for i in response["Images"]
    ]

    return sorted(images, key=lambda i: i["CreationDate"], reverse=True)


class Distro(str, Enum):
    amazon = "amazon"
    ubuntu = "ubuntu"

    def root_device(self, root_devices={"amazon": "/dev/xvda", "ubuntu": "/dev/sda1"}):
        return root_devices[self.name]


@app.command()
def launch(
    config=profile_option,
    name: str = typer.Argument(..., help="Name tag"),
    ami: str = typer.Argument(..., help="AMI id"),
    dist: Distro = typer.Option(Distro.amazon, help="Linux distribution"),
    volume_size: int = typer.Option(100, help="EBS volume size (GB)"),
    instance_type: str = typer.Option("t2.medium", help="Instance type"),
    key_name: Optional[str] = typer.Option(None, help="Key name"),
    userdata: Optional[Path] = typer.Option(None, help="Path to user data file"),
) -> List[Dict[str, Any]]:
    """
    Launch a tagged EC2 instance with an EBS volume
    """
    ec2_client = boto3.client("ec2", region_name=config["region"])

    additional_tags = config["additional_tags"] if config.get("additional_tags", None) else {}

    tags = [{"Key": "Name", "Value": name}] + [{"Key": k, "Value": v} for k, v in additional_tags.items()]

    root_device = dist.root_device()

    security_group = config["vpc"]["security_group"]

    if not key_name:
        key_name = config["key_name"]

    # TODO: support multiple subnets
    kwargs = {
        "ImageId": ami,
        "MaxCount": 1,
        "MinCount": 1,
        "KeyName": key_name,
        "InstanceType": instance_type,
        "TagSpecifications": [{"ResourceType": "instance", "Tags": tags}, {"ResourceType": "volume", "Tags": tags},],
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
                "DeviceName": root_device,
                "Ebs": {"VolumeSize": volume_size, "DeleteOnTermination": True, "VolumeType": "gp2",},
            }
        ],
    }

    associate_public_ip_address = config["vpc"].get("associate_public_ip_address", None)
    if associate_public_ip_address is not None:
        kwargs["NetworkInterfaces"][0]["AssociatePublicIpAddress"] = associate_public_ip_address

    iam_instance_profile_arn = config.get("iam_instance_profile_arn", None)
    if iam_instance_profile_arn:
        kwargs["IamInstanceProfile"] = {"Arn": iam_instance_profile_arn}

    if userdata:
        kwargs["UserData"] = read_file(userdata)

    print(f"Launching a {instance_type} in {config['region']} named {name} in " f"vpc {config['vpc']['name']}... ")
    response = ec2_client.run_instances(**kwargs)

    instance = response["Instances"][0]

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance["InstanceId"]])

    # TODO: wait until instance checks passed (as they do in the console)

    # the response from run_instances above always contains an empty string
    # for PublicDnsName, so we call describe to get it
    return describe(name=name, config=config)


@app.command()
def describe(
    name: Optional[str] = typer.Argument(default=None, help="Filter to hosts with this exact Name tag"),
    config=profile_option,
) -> List[Dict[str, Any]]:
    """
    List EC2 instances in the region
    """
    ec2_client = boto3.client("ec2", region_name=config["region"])

    filters = [] if name is None else [{"Name": "tag:Name", "Values": [name]}]
    response = ec2_client.describe_instances(Filters=filters)

    # print(response["Reservations"][0]["Instances"][0])

    instances = [
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
    ]

    return sorted(instances, key=lambda i: i["State"] + str(i["Name"]))


@app.command()
def start(name: str = typer.Argument(..., help="Name tag of instance"), config=profile_option,) -> List[Dict[str, Any]]:
    """
    Start EC2 instances by name
    """
    ec2_client = boto3.client("ec2", region_name=config["region"])

    print(f"Starting instances with the name {name} ... ")

    instances = describe(name, config)

    if not instances:
        raise Exception(f"No instances named {name}")

    instance_ids = [instance["InstanceId"] for instance in instances]
    ec2_client.start_instances(InstanceIds=instance_ids)

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=instance_ids)

    return describe(name, config)


@arg("name", help="Name tag")
@cli
def stop(config, name) -> List[Dict[str, Any]]:
    """
    Stop EC2 instances by name
    """
    ec2_client = boto3.client("ec2", region_name=config["region"])

    instances = describe(name, config)

    if not instances:
        raise Exception(f"No instances named {name}")

    response = ec2_client.stop_instances(InstanceIds=[instance["InstanceId"] for instance in instances])

    return [{"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["StoppingInstances"]]


@arg("name", help="Name tag of instance")
@cli
def terminate(config, name) -> List[Dict[str, Any]]:
    """
    Terminate EC2 instances by name
    """
    ec2_client = boto3.client("ec2", region_name=config["region"])

    instances = describe(name, config)

    if not instances:
        raise Exception(f"No instances named {name}")

    response = ec2_client.terminate_instances(InstanceIds=[instance["InstanceId"] for instance in instances])

    return [
        {"State": i["CurrentState"]["Name"], "InstanceId": i["InstanceId"]} for i in response["TerminatingInstances"]
    ]


@arg("name", help="Name tag of instance")
@arg("type", help="Type of instance")
@cli
def modify(config, name, type) -> List[Dict[str, Any]]:
    """
    Change an instance's type
    """
    ec2_client = boto3.client("ec2", region_name=config["region"])

    instances = describe(name, config)

    if not instances:
        raise Exception(f"No instances named {name}")

    instance_id = instances[0]["InstanceId"]
    ec2_client.modify_instance_attribute(InstanceId=instance_id, InstanceType={"Value": type})

    return describe(name, config)


def first_or_else(l: List[Any], default: Any) -> Any:
    return l[0] if len(l) > 0 else default


def read_file(filepath) -> AnyStr:
    with open(os.path.expanduser(filepath)) as file:
        return file.read()


def main():
    app()


if __name__ == "__main__":
    main()
