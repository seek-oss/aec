import os.path
from typing import AnyStr, Union

import argh
import boto3
from argh import arg

from tools.cli import cli
from tools.config import *
from tools.display import *


@arg('--owners', help='filter to AMIs owned by these accounts', default='self', nargs='*')
@cli
def describe_images(config, owners: Union[str, List[str]]) -> List[Dict[str, Any]]:
    """
    List AMIs owned by your account
    """

    ec2_client = boto3.client('ec2', region_name=config['region'])

    if isinstance(owners, str):
        owners = [owners]

    response = ec2_client.describe_images(Owners=owners)

    images = [{
        'ImageId': i['ImageId'],
        'Name': i.get('Name', None),
        'Description': i.get('Description', None),
        'CreationDate': i['CreationDate']
    } for i in response['Images']]

    return sorted(images, key=lambda i: i['CreationDate'], reverse=True)


root_devices = {
    'amazon': '/dev/xvda',
    'ubuntu': '/dev/sda1'
}


@arg('name', help='Name tag')
@arg('ami', help='ami id')
@arg('--dist', help='linux distribution', choices=root_devices.keys(), default='amazon')
@arg('--volume-size', help='ebs volume size (GB)', default=100)
@arg('--instance-type', help='instance type', default='t2.medium')
@arg('--userdata', help='path to user data file', default=None)
@cli
def launch(config, name: str, ami: str, dist: str = 'amazon', volume_size: int = 100, instance_type='t2.medium',
           userdata=None) -> \
        List[Dict[str, Any]]:
    """
    Launch a tagged EC2 instance with an EBS volume
    """
    ec2_client = boto3.client('ec2', region_name=config['region'])

    owner = config['owner']
    root_device = root_devices[dist]

    # TODO: support multiple subnets
    kwargs = {
        'ImageId': ami,
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
             'SubnetId': config['vpc']['subnet'], 'Ipv6AddressCount': 0,
             'Groups': [config['vpc']['security_group']]}
        ],
        'BlockDeviceMappings': [
            {'DeviceName': root_device,
             'Ebs': {'VolumeSize': volume_size, 'DeleteOnTermination': True, 'VolumeType': 'gp2'}}
        ]
    }
    if userdata:
        kwargs['UserData'] = read_file(userdata)

    print(
        f"Launching a {instance_type} in {config['region']} named {name} using {ami} in "
        f"vpc {config['vpc']['name']}... ")
    response = ec2_client.run_instances(**kwargs)

    instance = response['Instances'][0]

    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance['InstanceId']])

    return [{'InstanceType': instance['InstanceType'],
             'PrivateDnsName': instance['PrivateDnsName'],
             'ImageId': instance['ImageId'],
             'InstanceId': instance['InstanceId']}]


@arg('--name', help='Filter to hosts with this Name tag', default=None)
@cli
def describe(config, name=None) -> List[Dict[str, Any]]:
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
        'DnsName': i['PublicDnsName'] if i.get('PublicDnsName', None) != "" else i['PrivateDnsName'],
        'LaunchTime': i['LaunchTime'],
        'ImageId': i['ImageId'],
        'InstanceId': i['InstanceId']
    } for r in response['Reservations'] for i in r['Instances']]

    return sorted(instances, key=lambda i: i['State'] + str(i['Name']))


@arg('name', help='Name tag of instance')
@cli
def start(config, name) -> List[Dict[str, Any]]:
    """
    Start EC2 instance(s)
    """
    ec2_client = boto3.client('ec2', region_name=config['region'])

    print(f"Starting instance(s) with the name {name} ... ")

    instances = describe(config, name)
    instance_ids = [instance['InstanceId'] for instance in instances]
    ec2_client.start_instances(InstanceIds=instance_ids)

    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=instance_ids)

    return describe(config, name)


@arg('name', help='Name tag')
@cli
def stop(config, name) -> List[Dict[str, Any]]:
    """
    Stop EC2 instance(s)
    """
    ec2_client = boto3.client('ec2', region_name=config['region'])

    instances = describe(config, name)
    response = ec2_client.stop_instances(InstanceIds=[instance['InstanceId'] for instance in instances])

    return [{
        'State': i['CurrentState']['Name'],
        'InstanceId': i['InstanceId']
    } for i in response['StoppingInstances']]


@arg('name', help='Name tag of instance')
@cli
def terminate(config, name) -> List[Dict[str, Any]]:
    """
    Terminate EC2 instance(s)
    """
    ec2_client = boto3.client('ec2', region_name=config['region'])

    instances = describe(config, name)
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


def main():
    parser = argh.ArghParser()
    parser.add_commands([describe_images, describe, launch, start, stop, terminate])
    parser.dispatch()


if __name__ == '__main__':
    main()
