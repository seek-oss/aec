#!/usr/bin/env python

import fire
import boto3

defaults = {
    "syd":
        {
            "region": "ap-southeast-2",
            "amis": {"amazon_linux_2": "ami-04481c741a0311bbb",
                    "ubuntu": "ami-0b76c3b150c6b1423"
                    # TODO: automatically determine latest image
                    },

            "key_name": "my-key",

            "security_group": "sg-12345678901234567",

            # TODO: multiple subnets
            "subnet": "subnet-12345678",


            "iam_instance_profile_arn": "arn:aws:iam::123456789012:instance-profile/ec2_my_default"
        }
}


def launch(name, owner, volume_size=100, ami_name="gami", instance_type="t2.medium", region="ap-southeast-2",
           configs=configs):
    ec2_client = boto3.client('ec2', region_name=region)

    config = configs[region]

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


if __name__ == '__main__':
    fire.Fire()
