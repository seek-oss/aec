from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

import boto3
import pytz
from dateutil import relativedelta

if TYPE_CHECKING:
    from mypy_boto3_compute_optimizer.type_defs import UtilizationMetricTypeDef

from aec.util.config import Config


def over_provisioned(config: Config) -> List[Dict[str, Any]]:
    """Show recommendations for over-provisioned EC2 instances."""

    def util(metric: UtilizationMetricTypeDef) -> str:
        return f'{metric["name"]} {metric["statistic"][:3]} {metric["value"]}'

    instances_uptime = describe_instances_uptime(config)

    client = boto3.client("compute-optimizer", region_name=config.get("region", None))

    response = client.get_ec2_instance_recommendations(filters=[{"name": "Finding", "values": ["Overprovisioned"]}])

    recs = [
        {
            "ID": i["instanceArn"].split("/")[1],
            "Name": i.get("instanceName", None),
            "Instance Type": i["currentInstanceType"],
            "Recommendation": i["recommendationOptions"][0]["instanceType"],
            "Utilization": util(i["utilizationMetrics"][0]),
            "Uptime": instances_uptime[i["instanceArn"].split("/")[1]],
        }
        for i in response["instanceRecommendations"]
    ]

    return recs


def describe_instances_uptime(config: Config) -> Dict[str, str]:
    """List EC2 instance uptimes in the region."""

    ec2_client = boto3.client("ec2", region_name=config.get("region", None))

    response = ec2_client.describe_instances()

    instances = {
        i["InstanceId"]: difference_in_words(datetime.now(pytz.utc), i["LaunchTime"])
        for r in response["Reservations"]
        for i in r["Instances"]
    }

    return instances


def difference_in_words(date1: datetime, date2: datetime) -> str:
    difference = relativedelta.relativedelta(date1, date2)

    words = ""

    if difference.months > 0:
        words += f"{difference.months} months "
    if difference.days > 0:
        words += f"{difference.days} days "
    if difference.hours > 0:
        words += f"{difference.hours} hours "
    if words == "":
        if difference.minutes != 0:
            words = f"{difference.minutes} minutes"
        else:
            words = f"{difference.seconds} seconds"

    return words
