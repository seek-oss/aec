from typing import Any, Dict, List

import boto3
import aec.command.ec2 as ec2


def describe(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Describe instances running the SSM agent."""

    instances_names = ec2.describe_instances_names(config)

    client = boto3.client("ssm", region_name=config["region"])

    response = client.describe_instance_information()

    instances = [
        {
            "ID": i["InstanceId"],
            "Name": instances_names.get(i["InstanceId"], None),
            "PingStatus": i["PingStatus"],
            "Platform": f'{i["PlatformName"]} {i["PlatformVersion"]}',
            "AgentVersion": i["AgentVersion"],
        }
        for i in response["InstanceInformationList"]
    ]

    return instances

