<!-- [[[cog
import cog
from aec.util.docgen import docs
from aec.util.docgen import mock_aws_config as config
import aec.command.ec2 as ec2
]]] -->
<!-- [[[end]]] -->

# EC2 Usage

Run `aec ec2 -h` for help:

<!-- [[[cog
from aec.main import build_parser
cog.out(f"```\n{build_parser()._subparsers._actions[1].choices['ec2'].format_help()}```")
]]] -->
```
usage: aec ec2 [-h] {create-key-pair,describe,launch,logs,modify,start,stop,restart,sec-groups,subnets,rename,tag,tags,status,templates,terminate,user-data} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {create-key-pair,describe,launch,logs,modify,start,stop,restart,sec-groups,subnets,rename,tag,tags,status,templates,terminate,user-data}
    create-key-pair     Create a key pair.
    describe            List EC2 instances in the region.
    launch              Launch a tagged EC2 instance with an EBS volume.
    logs                Show the system logs.
    modify              Change an instance's type.
    start               Start EC2 instance.
    stop                Stop EC2 instance.
    restart             Restart EC2 instance, optionally changing the instance type.
    sec-groups          Describe security groups in the region, optionally filtered by VPC ID.
    subnets             Describe subnets.
    rename              Rename EC2 instance(s).
    tag                 Tag EC2 instance(s).
    tags                List EC2 instances or volumes with their tags.
    status              Describe instances status checks.
    templates           Describe launch templates.
    terminate           Terminate EC2 instance.
    user-data           Describe user data for an instance.
```
<!-- [[[end]]] -->

Launch an instance named `food baby` from the [ec2 launch template](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-templates.html) named `yummy`:

```
aec ec2 launch "food baby" --template yummy
```

Launch a t2.medium instance named `lady gaga` with a 50gb EBS volume, userdata, and other settings read from the config file:

```
aec ec2 launch "lady gaga" --ami ubuntu2004 --instance-type t2.medium --volume-size 50 --userdata https://raw.githubusercontent.com/tekumara/setup-ubuntu/main/setup-ubuntu.yaml
```

Stop the instance:

```
aec ec2 stop "lady gaga"
```

Modify the instance type:

```
aec ec2 modify "lady gaga" p2.xlarge
```

Start a stopped instance, and wait for the SSM agent to come online (at which point SSH will be available):

```
aec ec2 start "lady gaga" -w
```

Restart an instance and change the instance type:
```
aec ec2 restart "lady gaga" -t m5.large
```

List all instances in the region:

<!-- [[[cog
cog.out(f"```\n{docs('aec ec2 describe', ec2.describe(config))}\n```")
]]] -->
```
aec ec2 describe
                                                                                                                                            
  InstanceId            State     Name    Type       DnsName                                      LaunchTime                  ImageId       
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  i-a6c907a7659c657ec   running   alice   t3.small   ec2-54-214-143-173.compute-1.amazonaws.com   2025-04-01 22:53:13+00:00   ami-03cf127a  
  i-10775ea95215edd19   running   sam     t3.small   ec2-54-214-92-78.compute-1.amazonaws.com     2025-04-01 22:53:13+00:00   ami-03cf127a
```
<!-- [[[end]]] -->

List instances containing `gaga` in the name:

```
aec ec2 describe -q gaga
```

By default, commands will use the default profile as specified in the config file (_~/.aec/ec2.toml_). To list ec2 instances using the non-default config `us`:

```
aec ec2 describe --config us
```

Show running or pending instances only:

```
aec ec2 describe -r
```

Show running instances sorted by date started (ie: LaunchTime), oldest first:

```
aec ec2 describe -r -s LaunchTime
```

Show a custom set of [columns](#columns):

<!-- [[[cog
cog.out(f"```\n{docs('aec ec2 describe -c Name,SubnetId,Volumes,Image.CreationDate', ec2.describe(config, columns='Name,SubnetId,Volumes,Image.CreationDate'))}\n```")
]]] -->
```
aec ec2 describe -c Name,SubnetId,Volumes,Image.CreationDate
                                                                                 
  Name    SubnetId                   Volumes           Image.CreationDate        
 ─────────────────────────────────────────────────────────────────────────────── 
  alice   subnet-7c7eebe4933bd527a   ['Size=15 GiB']   2025-04-01T22:53:13.000Z  
  sam     subnet-7c7eebe4933bd527a   ['Size=15 GiB']   2025-04-01T22:53:13.000Z
```
<!-- [[[end]]] -->

Show instances and all their tags:

```
aec ec2 tags

  InstanceId            Name        Tags
 ────────────────────────────────────────────────────────────────
  i-099fe44f811245812   instance A  Name=instance A, Owner=alice
```

Show instances and just the value of the tags `Owner` and `Project`:

```
aec ec2 tags --keys Owner Project

  InstanceId            Name        Tag: Owner    Tag: Project
 ──────────────────────────────────────────────────────────────
  i-099fe44f811245812   instance A  alice         top secret
```

Show volume tags

```
aec ec2 tags -v

  VolumeId              Name          Tags
 ───────────────────────────────────────────────────────────────────
  vol-0439c5ed37f6d455e   awesome-vol   Name=awesome-vol, Owner=jane
```

Tag an instance

```
aec ec2 tag alice -t Project="top secret" -t keep=forever

  InstanceId            Name    Tag: Project   Tag: keep
 ──────────────────────────────────────────────────────────────────────
  i-0f7f6a072d985fd2d   alice   top secret     forever
```

Rename an instance

```
aec ec2 rename alice alice2
```

Show output as csv instead of a table (works with any command)

```
aec ec2 tags -v -o csv
VolumeId,Name,Tags
vol-0439c5ed37f6d455e,awesome-vol,"Name=awesome-vol, Owner=jane"
```

Show instances status checks:

```
aec ec2 status

  InstanceId            State     Name    System status check   Instance status check
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  i-178f32b2857e1ee7f   running   alice   reachability passed   reachability passed
  i-fa8cba40e84f2afae   running   sam     reachability passed   reachability failed since 2022-03-27 03:17:00+00:00
```

Terminate an instance using its id:

```
aec ec2 terminate i-06814ad77d5177e5a
```

Show reason for termination:

```
aec ec2 describe -it i-02a840e0ca609c432 -c StateReason

  StateReason
 ─────────────────────────────────────────────────────────────────────────────────────────────
  {'Code': 'Client.InternalError', 'Message': 'Client.InternalError: Client error on launch'}
```

Describe subnets:

<!-- [[[cog
cog.out(f"```\n{docs('aec ec2 subnets', ec2.subnets(config))}\n```")
]]] -->
```
aec ec2 subnets
                                                                                               
  SubnetId                   VpcId                   AvailabilityZone   CidrBlock        Name  
 ───────────────────────────────────────────────────────────────────────────────────────────── 
  subnet-7c7eebe4933bd527a   vpc-2d040ead29eee6cf8   us-east-1a         172.31.0.0/20          
  subnet-3961372401467a0d6   vpc-2d040ead29eee6cf8   us-east-1b         172.31.16.0/20         
  subnet-c174b5405eaf42d81   vpc-2d040ead29eee6cf8   us-east-1c         172.31.32.0/20         
  subnet-4d930d9329f0bcd9b   vpc-2d040ead29eee6cf8   us-east-1d         172.31.48.0/20         
  subnet-6029fe0fac51d968a   vpc-2d040ead29eee6cf8   us-east-1e         172.31.64.0/20         
  subnet-1dd87fc3fe137e5aa   vpc-2d040ead29eee6cf8   us-east-1f         172.31.80.0/20
```
<!-- [[[end]]] -->

Describe security groups:

<!-- [[[cog
cog.out(f"```\n{docs('aec ec2 sec-groups', ec2.sec_groups(config))}\n```")
]]] -->
```
aec ec2 sec-groups
                                                                                         
  GroupId                GroupName   Description                  VpcId                  
 ─────────────────────────────────────────────────────────────────────────────────────── 
  sg-af760af3a4fc243fe   default     default VPC security group   vpc-2d040ead29eee6cf8  
  default                default     default                      vpc-2d040ead29eee6cf8
```
<!-- [[[end]]] -->

## Columns

Columns special to aec:

- `DnsName` - PublicDnsName if available otherwise PrivateDnsName
- `Name` - Name tag
- `State` - state name
- `Type` - instance type
- `Volumes` - volumes attached to the instance
- `Image.X` - where `X` is a field from the Image, eg: `Image.CreationDate`. See more below.

[Instance columns](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ec2/type_defs/#instancetypedef) returned by the EC2 API you can use:

```
AmiLaunchIndex
Architecture
BlockDeviceMappings
CapacityReservationSpecification
ClientToken
CpuOptions
CurrentInstanceBootMode
EbsOptimized
EnaSupport
EnclaveOptions
HibernationOptions
Hypervisor
IamInstanceProfile
ImageId
InstanceId
InstanceType
KeyName
LaunchTime
MaintenanceOptions
MetadataOptions
Monitoring
NetworkInterfaces
Placement
PlatformDetails
PrivateDnsName
PrivateDnsNameOptions
PrivateIpAddress
ProductCodes
PublicDnsName
RootDeviceName
RootDeviceType
SecurityGroups
SourceDestCheck
State
StateTransitionReason
SubnetId
Tags
UsageOperation
UsageOperationUpdateTime
VirtualizationType
VpcId
```

[Image columns](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ec2/type_defs/#imagetypedef) returned by the EC2 API you can use with the `Image.` suffix:

```
Architecture
CreationDate
ImageId
ImageLocation
ImageType
Public
KernelId
OwnerId
Platform
PlatformDetails
UsageOperation
ProductCodes
RamdiskId
State
BlockDeviceMappings
Description
EnaSupport
Hypervisor
ImageOwnerAlias
Name
RootDeviceName
RootDeviceType
SriovNetSupport
StateReason
Tags
VirtualizationType
BootMode
TpmSupport
DeprecationTime
ImdsSupport
```
