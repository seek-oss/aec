from typing import Any, Dict, List

import boto3


def describe(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Describe instances with the SSM agent."""

    client = boto3.client("ssm", region_name=config["region"])

    response = client.describe_instance_information()

    instances = [
        {
            "ID": i["InstanceId"],
            "PingStatus": i["PingStatus"],
            "PlatformName": i["PlatformName"],
            "PlatformVersion": i["PlatformVersion"],
        }
        for i in response["InstanceInformationList"]
    ]

    return instances

