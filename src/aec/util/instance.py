from typing import List, Optional, TypeVar, Union

from mypy_boto3_ec2.type_defs import InstanceTypeDef

E = TypeVar("E")
T = TypeVar("T")


def first_or_else(li: List[E], default: T) -> Union[E, T]:
    return li[0] if li else default


def name(instance: InstanceTypeDef) -> Optional[str]:
    return first_or_else([t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"], None)
