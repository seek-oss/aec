from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from mypy_boto3_ec2.type_defs import ImageTypeDef, InstanceTypeDef, VolumeTypeDef


def get_value(resource: ImageTypeDef | InstanceTypeDef | VolumeTypeDef, key: str) -> Optional[str]:
    tag_value = [t["Value"] for t in resource.get("Tags", []) if t["Key"] == key]
    return tag_value[0] if tag_value else None
