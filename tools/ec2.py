#!/usr/bin/env python
import os.path
from typing import AnyStr

import boto3
from argh import arg

from cli import cli
from config import *
from display import *


@cli
def describe_images(config) -> List[Dict[str, Any]]:
    """
    List AMIs owned by your account
    """

    ec2_client = boto3.client('ec2', region_name=config['region'])

    response = ec2_client.describe_images(Owners=['self'])

    images = [{
        'ImageId': i['ImageId'],
        'Name': i['Name'],
        'Description': i.get('Description', None),
        'CreationDate': i['CreationDate']
    } for i in response['Images']]

    return sorted(images, key=lambda i: i['CreationDate'], reverse=True)


def launch(ctx, name, owner, volume_size: int = 100, ami_name='gami', instance_type='t2.medium') -> Dict[str, Any]:
    """
    Launch a tagged EC2 instance with an EBS volume

    :param name: name tag
    :param owner: owner tag
    :param volume_size: ebs volume size (GB)
    :param ami_name: ami name (looked up in the config)
    :param instance_type: instance type
    :param config: config, see config.example
    :return:
    """
    config = ctx.obj['config']
    ec2_client = boto3.client('ec2', region_name=config['region'])

    ami = config['amis'][ami_name]
    # TODO: support multiple subnets
    kwargs = {
        'ImageId': ami['id'],
        'MaxCount': 1, 'MinCount': 1,
        'KeyName': config['key_name'],
        'InstanceType': instance_type,
        'IamInstanceProfile': {"Arn": config['iam_instance_profile_arn']},
        'TagSpecifications': [
            # TODO read owner and any other tags from the config file
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
            {'DeviceName': ami['root_device'],
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


@arg('--name', help='Filter to hosts with this Name tag', default=None)
@cli
def describe(config, name=None) -> List[Dict[str, any]]:
    """
    List EC2 instances in the region
    """
    ec2_client = boto3.client('ec2', region_name=config['region'])

    filters = [] if name is None else [{"Name": "tag:Name", "Values": [name]}]
    response = ec2_client.describe_instances(Filters=filters)

    instances = [{
        'State': i['State']['Name'],
        'Name': first_or_else([t['Value'] for t in i.get('Tags', []) if t['Key'] == 'Name'], None),
        'Type': i['InstanceType'],
        'PrivateDnsName': i['PrivateDnsName'],
        'LaunchTime': i['LaunchTime'],
        'ImageId': i['ImageId'],
        'InstanceId': i['InstanceId']
    } for r in response['Reservations'] for i in r['Instances']]

    return sorted(instances, key=lambda i: i['State']+str(i['Name']))


def stop(name, config=None) -> List[Dict[str, Any]]:
    """
    Stop EC2 instance(s)

    :param name:
    :param config:
    :return:
    """

    if config is None:
        config = user_config[user_config['default']]

    ec2_client = boto3.client('ec2', region_name=config['region'])

    instances = describe(name, config)
    response = ec2_client.stop_instances(InstanceIds=[instance['InstanceId'] for instance in instances])

    return [{
        'State': i['CurrentState']['Name'],
        'InstanceId': i['InstanceId']
    } for i in response['StoppingInstances']]


def terminate(name, config=None) -> List[Dict[str, Any]]:
    """
    Terminate EC2 instance(s)

    :param name:
    :param config:
    :return:
    """
    if config is None:
        config = user_config[user_config['default']]

    ec2_client = boto3.client('ec2', region_name=config['region'])

    instances = describe(name, config)
    response = ec2_client.terminate_instances(InstanceIds=[instance['InstanceId'] for instance in instances])

    return [{
        'State': i['CurrentState']['Name'],
        'InstanceId': i['InstanceId']
    } for i in response['TerminatingInstances']]


def first_or_else(l: List[Any], default: Any) -> Any:
    return l[0] if len(l) > 0 else default


def read_file(filepath) -> AnyStr:
    with open(os.path.expanduser(filepath)) as file:
        return file.read()
