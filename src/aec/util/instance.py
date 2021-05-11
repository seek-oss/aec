from typing import Optional

from mypy_boto3_ec2.type_defs import InstanceTypeDef


def tag(instance: InstanceTypeDef, key: str) -> Optional[str]:
    tag_value = [t["Value"] for t in instance.get("Tags", []) if t["Key"] == key]
    return tag_value[0] if tag_value else None
