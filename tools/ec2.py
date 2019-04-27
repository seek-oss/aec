#!/usr/bin/env python
import sys
from typing import Dict, Any, List

import fire
import boto3
import pytoml as toml
import os.path


def launch(name, owner, volume_size=100, ami_name='gami', instance_type='t2.medium', config=None) -> Dict[str, Any]:
    """
    Launch an EC2 instance

    :param name: name tag
    :param owner: owner tag
    :param volume_size: ebs volume size (GB)
    :param ami_name: ami name (looked up in the config)
    :param instance_type: instance type
    :param config: config, see config.example
    :return:
    """
    if config is None:
        config = user_config[user_config['default']]

    ec2_client = boto3.client('ec2', region_name=config['region'])

    # TODO: support multiple subnets
    kwargs = {
        'ImageId': config['amis'][ami_name],
        'MaxCount': 1, 'MinCount': 1,
        'KeyName': config['key_name'],
        'InstanceType': instance_type,
        'IamInstanceProfile': {"Arn": config['iam_instance_profile_arn']},
        'TagSpecifications': [
            {'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': name}, {'Key': 'Owner', 'Value': owner}]},
            {'ResourceType': 'volume', 'Tags': [{'Key': 'Name', 'Value': name}, {'Key': 'Owner', 'Value': owner}]}
        ],
        'EbsOptimized': False if instance_type.startswith("t2") else True,
        'NetworkInterfaces': [
            {'DeviceIndex': 0, 'Description': 'Primary network interface', 'DeleteOnTermination': True,
             'SubnetId': config['subnet'], 'Ipv6AddressCount': 0,
             'Groups': [config['security_group']]}
        ],
        'BlockDeviceMappings': [
            {'DeviceName': '/dev/xvda',
             'Ebs': {'VolumeSize': volume_size, 'DeleteOnTermination': True, 'VolumeType': 'gp2'}}
        ]
    }
    if config.get('userdata', None) and config['userdata'].get(ami_name, None):
        kwargs['UserData'] = read_file(config['userdata'][ami_name])

    print(f"Launching a {instance_type} in {config['region']} with name {name} ... ")
    response = ec2_client.run_instances(**kwargs)

    instance = response['Instances'][0]

    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance['InstanceId']])

    return {'InstanceType': instance['InstanceType'],
            'PrivateDnsName': instance['PrivateDnsName'],
            'LaunchTime': instance['LaunchTime'],
            'ImageId': instance['ImageId'],
            'InstanceId': instance['InstanceId']}


def describe(config=None) -> Dict[str, Any]:
    """
    List all the EC2 instances in the region

    :param config: config, see config.example
    :return:
    """
    if config is None:
        config = user_config[user_config['default']]

    ec2_client = boto3.client('ec2', region_name=config['region'])

    response = ec2_client.describe_instances()

    instances = [{
        'State': i['State']['Name'],
        'Name': first_or_else([t['Value'] for t in i['Tags'] if t['Key'] == 'Name'], None),
        'Type': i['InstanceType'],
        'PrivateDnsName': i['PrivateDnsName'],
        'LaunchTime': i['LaunchTime'],
        'ImageId': i['ImageId'],
        'InstanceId': i['InstanceId']
    } for r in response['Reservations'] for i in r['Instances']]

    return instances


def first_or_else(l: List[Any], default: Any) -> Any:
    return l[0] if len(l) > 0 else default


def read_file(filepath) -> str:
    with open(os.path.expanduser(filepath)) as file:
        return file.read()


def load_user_config() -> Dict[str, Any]:
    filepath = os.path.expanduser('~/.aww/config')
    if not os.path.isfile(filepath):
        print(f"WARNING: No file {filepath}", file=sys.stderr)
        return

    with open(filepath) as config_file:
        return toml.load(config_file)


if __name__ == '__main__':
    user_config = load_user_config()
    fire.Fire()
