from typing import Any, Dict, List

import boto3
from mypy_boto3_compute_optimizer.type_defs import UtilizationMetricTypeDef


def over_provisioned(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Show recommendations for over-provisioned EC2 instances."""

    def util(metric: UtilizationMetricTypeDef) -> str:
        return f'{metric["name"]} {metric["statistic"][:3]} {metric["value"]}'

    client = boto3.client("compute-optimizer", region_name=config["region"])

    response = client.get_ec2_instance_recommendations(filters=[{"name": "Finding", "values": ["Overprovisioned"]}])

    recs = [
        {
            "ID": i["instanceArn"].split("/")[1],
            "Name": i.get("instanceName", None),
            "Instance Type": i["currentInstanceType"],
            "Recommendation": i["recommendationOptions"][0]["instanceType"],
            "Utilization": util(i["utilizationMetrics"][0]),
        }
        for i in response["instanceRecommendations"]
    ]

    return recs
