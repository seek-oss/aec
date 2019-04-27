#!/usr/bin/env python
import sys
from typing import Dict, Any

import fire
import boto3
import pytoml as toml
import os.path


def launch(name, owner, volume_size=100, ami_name="gami", instance_type="t2.medium", config=None) -> Dict[str, Any]:
    if config is None:
        config = user_config[user_config["default"]]

    ec2_client = boto3.client('ec2', region_name=config["region"])

    # TODO: support multiple subnets
    response = ec2_client.run_instances(
        ImageId=config['amis'][ami_name],
        MaxCount=1, MinCount=1,
        KeyName=config['key_name'],
        InstanceType=instance_type,
        IamInstanceProfile={"Arn": config['iam_instance_profile_arn']},
        TagSpecifications=[
            {'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': name}, {'Key': 'Owner', 'Value': owner}]},
            {'ResourceType': 'volume', 'Tags': [{'Key': 'Name', 'Value': name}, {'Key': 'Owner', 'Value': owner}]}
        ],
        EbsOptimized=False if instance_type.startswith("t2") else True,
        NetworkInterfaces=[
            {'DeviceIndex': 0, 'Description': 'Primary network interface', 'DeleteOnTermination': True,
             'SubnetId': config['subnet'], 'Ipv6AddressCount': 0,
             'Groups': [config['security_group']]}
        ],
        BlockDeviceMappings=[
            {'DeviceName': '/dev/xvda',
             'Ebs': {'VolumeSize': volume_size, 'DeleteOnTermination': True, 'VolumeType': 'gp2'}}
        ]
    )

    instance = response['Instances'][0]

    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance['InstanceId']])

    return {'InstanceType': instance['InstanceType'],
            'PrivateDnsName': instance['PrivateDnsName'],
            'LaunchTime': instance['LaunchTime'],
            'ImageId': instance['ImageId'],
            'InstanceId': instance['InstanceId']}


def load_user_config() -> Dict[str, Any]:
    filepath = os.path.expanduser('~/.aww/config')
    if not os.path.isfile(filepath):
        print(f"WARNING: No file {filepath}", file=sys.stderr)
        return

    with open(filepath, 'rb') as config_file:
        return toml.load(config_file)


if __name__ == '__main__':
    user_config = load_user_config()
    fire.Fire()
