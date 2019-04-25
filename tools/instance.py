import fire
import boto3


config = {
    "ami": {"amazon_linux_2": "ami-04481c741a0311bbb",
            "ubuntu": "ami-0b76c3b150c6b1423"
            # TODO: automatically determine latest image
            },

    "key_name": {"ap-southeast-2": "my-key"},

    "security_group": {"ap-southeast-2": "sg-12345678901234567"},

    # TODO: multiple subnets
    "subnet": {"ap-southeast-2": "subnet-12345678"}
}


def launch(name, owner, volume_size=100, ami_name="amazon_linux_2", instance_type="t2.medium", region="ap-southeast-2",
           config=config):
    ec2_client = boto3.client('ec2', region_name=region)

    response = ec2_client.run_instances(
        ImageId=config['ami'][ami_name],
        MaxCount=1, MinCount=1,
        KeyName=config['key_name'][region],
        InstanceType=instance_type,
        TagSpecification=[
            {'ResourceType': 'instance', 'Tag': [{'Key': 'Name', 'Value': name}, {'Key': 'Owner', 'Value': owner}]},
            {'ResourceType': 'volume', 'Tag': [{'Key': 'Name', 'Value': name}, {'Key': 'Owner', 'Value': owner}]}
        ],
        EbsOptimized=True,
        NetworkInterfaces=[
            {'DeviceIndex': 0, 'Description': 'Primary network interface', 'DeleteOnTermination': True,
             'SubnetId': config['subnet'][region], 'Ipv6AddressCount': 0,
             'GroupSet': [config['security_group'][region]]}
        ],
        BlockDeviceMappings=[
            {'DeviceName': '/dev/xvda',
             'Ebs': {'VolumeSize': volume_size, 'DeleteOnTermination': True, 'VolumeType': 'gp2'}}
        ]
    )

    instance_id = response['Instances'][0]['InstanceId']

    return response


def hello():
    print("hello")


def world():
    print("world")


if __name__ == '__main__':
    fire.Fire([launch, hello, world])
