from __future__ import annotations

from typing import TYPE_CHECKING, List, NamedTuple, Optional

import boto3

if TYPE_CHECKING:
    from mypy_boto3_ec2.type_defs import FilterTypeDef

from typing_extensions import NotRequired, TypedDict

from aec.util.config import Config


class Image(TypedDict):
    Name: Optional[str]
    ImageId: str
    CreationDate: str
    RootDeviceName: Optional[str]
    Size: Optional[int]
    SnapshotId: NotRequired[str]


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


def fetch(config: Config, ami: str) -> Image:
    ami_matcher = ami_keywords.get(ami, None)
    if ami_matcher:
        try:
            # lookup the latest ami by name match
            ami_details = describe(config, owner=ami_matcher.owner, name_match=ami_matcher.match_string)[0]
        except IndexError:
            raise RuntimeError(
                f"Could not find ami with name matching {ami_matcher.match_string} owned by account {ami_matcher.owner}"
            )
    else:
        try:
            # lookup by ami id
            ami_details = describe(config, ami=ami)[0]
        except IndexError:
            raise RuntimeError(f"Could not find {ami}")
    return ami_details


def describe(
    config: Config,
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

        print(f'Describing images owned by {owners_filter} with name matching {name_match or "*"}')

        response = ec2_client.describe_images(Owners=owners_filter, Filters=filters)

    images = []
    for i in response["Images"]:
        image: Image = {
            "Name": i.get("Name", None),
            "ImageId": i["ImageId"],
            "CreationDate": i["CreationDate"],
            "RootDeviceName": i["RootDeviceName"] if "RootDeviceName" in i else None,
            "Size": i["BlockDeviceMappings"][0]["Ebs"]["VolumeSize"] if i["BlockDeviceMappings"] else None,
        }
        if show_snapshot_id:
            image["SnapshotId"] = i["BlockDeviceMappings"][0]["Ebs"]["SnapshotId"]
        images.append(image)

    return sorted(images, key=lambda i: i["CreationDate"], reverse=True)


def delete(config: Config, ami: str) -> None:
    """Deregister an AMI and delete its snapshot."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = describe(config, ami, show_snapshot_id=True)

    ec2_client.deregister_image(ImageId=ami)

    ec2_client.delete_snapshot(SnapshotId=response[0]["SnapshotId"])


def share(config: Config, ami: str, account: str) -> None:
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
