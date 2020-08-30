from typing import Any, Dict, List

import boto3



def describe(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Describe instances running the SSM agent."""

    instances_names = describe_instances_names(config)

    client = boto3.client("ssm", region_name=config.get("region", None))

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

def describe_instances_names(config: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """List EC2 instance names in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances()

    instances = {
        i["InstanceId"]: first_or_else([t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"], None)
        for r in response["Reservations"]
        for i in r["Instances"]
    }

    return instances