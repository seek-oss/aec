from typing import Any, Dict, List
import boto3


def over_provisioned(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """ Return recommendations for over-provisioned EC2 instances. """

    client = boto3.client("compute-optimizer", region_name=config["region"])

    response = client.get_ec2_instance_recommendations(filters=[{"name": "Finding", "values": ["Overprovisioned"]}])

    recs = [
        {
            "ID": i["instanceArn"].split("/")[1],
            "Name": i.get("instanceName", None),
            "Instance Type": i["currentInstanceType"],
            "Recommendation": i["recommendationOptions"][0]["instanceType"]
        }
        for i in response["instanceRecommendations"]
    ]

    return recs