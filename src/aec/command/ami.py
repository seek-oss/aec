from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple, Sequence

import boto3

if TYPE_CHECKING:
    from mypy_boto3_ec2.type_defs import DescribeImagesResultTypeDef, FilterTypeDef

from typing_extensions import NotRequired, TypedDict

import aec.util.tags as util_tags
from aec.util.config import Config


class Image(TypedDict):
    Name: str | None
    ImageId: str
    CreationDate: str
    RootDeviceName: str | None
    Size: int | None
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
    "ubuntu2204": AmiMatcher(canonical_account_id, "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64"),
}


def fetch(config: Config, ami: str) -> Image:
    ami_matcher = ami_keywords.get(ami)
    if ami_matcher:
        try:
            # lookup the latest ami by name match
            ami_details = describe(config, owner=ami_matcher.owner, name_match=ami_matcher.match_string)[0]
        except IndexError:
            raise RuntimeError(
                f"Could not find ami with name matching {ami_matcher.match_string} owned by account {ami_matcher.owner}"
            ) from None
    else:
        try:
            # lookup by ami id
            ami_details = describe(config, ident=ami)[0]
        except IndexError:
            raise RuntimeError(f"Could not find {ami}") from None
    return ami_details


def _describe_images(
    config: Config,
    ident: str | None = None,
    owner: str | None = None,
    name_match: str | None = None,
) -> DescribeImagesResultTypeDef:
    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    if ident and ident.startswith("ami-"):
        return ec2_client.describe_images(ImageIds=[ident])
    if owner:
        owners_filter = [owner]
    else:
        describe_images_owners = config.get("describe_images_owners", None)

        if not describe_images_owners:
            owners_filter = ["self"]
        elif isinstance(describe_images_owners, str):
            owners_filter = [describe_images_owners]
        else:
            owners_filter: list[str] = describe_images_owners

    if name_match is None:
        name_match = config.get("describe_images_name_match", None)

    if name_match is None:
        filters = [{"Name": "name", "Values": [f"{ident}"]}] if ident else []
        match_desc = f" named {ident}" if ident else ""
    else:
        filters: list[FilterTypeDef] = [{"Name": "name", "Values": [f"*{name_match}*"]}]
        match_desc = f" with name containing {name_match}"

    print(f"Describing images owned by {owners_filter}{match_desc}")

    return ec2_client.describe_images(Owners=owners_filter, Filters=filters)


def describe(
    config: Config,
    ident: str | None = None,
    owner: str | None = None,
    name_match: str | None = None,
    show_snapshot_id: bool = False,
) -> list[Image]:
    """List AMIs."""

    response = _describe_images(config, ident, owner, name_match)

    images = []
    for i in response["Images"]:
        image: Image = {
            "Name": i.get("Name", None),
            "ImageId": i["ImageId"],
            "CreationDate": i["CreationDate"],
            "RootDeviceName": i.get("RootDeviceName", None),
            "Size": i["BlockDeviceMappings"][0]["Ebs"]["VolumeSize"] if i["BlockDeviceMappings"] else None,
        }
        if show_snapshot_id:
            image["SnapshotId"] = i["BlockDeviceMappings"][0]["Ebs"]["SnapshotId"]
        images.append(image)

    return sorted(images, key=lambda i: i["CreationDate"], reverse=True)


def describe_tags(
    config: Config,
    ident: str | None = None,
    owner: str | None = None,
    name_match: str | None = None,
    keys: Sequence[str] = [],
) -> list[dict[str, Any]]:
    """List AMI images with their tags."""

    response = _describe_images(config, ident, owner, name_match)

    images = []
    for i in response["Images"]:
        image = {"ImageId": i["ImageId"], "Name": util_tags.get_value(i, "Name")}
        if not keys:
            image["Tags"] = ", ".join(f"{tag['Key']}={tag['Value']}" for tag in i.get("Tags", []))
        else:
            for key in keys:
                image[f"Tag: {key}"] = util_tags.get_value(i, key)

        images.append(image)

    return sorted(images, key=lambda i: str(i["Name"]))


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
