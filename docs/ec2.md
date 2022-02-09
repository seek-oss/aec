# EC2 Usage

Run `aec ec2 -h` for help:

```
usage: aec ec2 [-h] {create-key-pair,describe,launch,logs,modify,start,stop,tag,tags,templates,terminate} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {create-key-pair,describe,launch,logs,modify,start,stop,tag,tags,templates,terminate}
    create-key-pair     Create a key pair.
    describe            List EC2 instances in the region.
    launch              Launch a tagged EC2 instance with an EBS volume.
    logs                Show the system logs.
    modify              Change an instance's type.
    start               Start EC2 instance.
    stop                Stop EC2 instance.
    tag                 Tag EC2 instance(s).
    tags                List EC2 instances or volumes with their tags.
    templates           Describe launch templates.
    terminate           Terminate EC2 instance.
```

Launch an instance named `food baby` from the [ec2 launch template](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-templates.html) named `yummy`:

```
aec ec2 launch "food baby" --template yummy
```

Launch a t2.medium instance named `lady gaga` with a 50gb EBS volume, with other settings read from the config file:

```
aec ec2 launch "lady gaga" --ami ubuntu1804 --instance-type t2.medium --volume-size 50
```

Stop the instance:

```
aec ec2 stop "lady gaga"
```

Modify the instance type:

```
aec ec2 modify "lady gaga" p2.xlarge
```

List all instances in the region:

```
aec ec2 describe

  InstanceId            State     Name    Type       DnsName                   LaunchTime                 ImageId
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  i-db2e4e24c95fa5ed7   running   alice   t3.small   ec2-54-214-178-132.com…   2022-02-09                 ami-03cf127a
                                                                               09:46:44+00:00
  i-a91307a999f4309be   running   sam     t3.small   ec2-54-214-170-196.com…   2022-02-09                 ami-03cf127a
                                                                               09:46:44+00:00
```

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
ec2 describe -r
```

Show running instances sorted by date started (ie: LaunchTime), oldest first:

```
ec2 describe -r -s LaunchTime
```

Show a custom set of columns

```
ec2 describe -c SubnetId,Name
```

Show instances and all their tags:

```
ec2 tags

  InstanceId            Name        Tags
 ────────────────────────────────────────────────────────────────
  i-099fe44f811245812   instance A  Name=instance A, Owner=alice
```

Show instances and just the value of the tags `Owner` and `Project`:

```
ec2 tags --keys Owner Project

  InstanceId            Name        Tag: Owner    Tag: Project
 ──────────────────────────────────────────────────────────────
  i-099fe44f811245812   instance A  alice         top secret
```

Show volume tags

```
ec2 tags -v

  VolumeId              Name          Tags
 ───────────────────────────────────────────────────────────────────
  vol-0439c5ed37f6d455e   awesome-vol   Name=awesome-vol, Owner=jane
```

Tag an instance

```
ec2 tag alice -t Project="top secret" keep=forever

  InstanceId            Name    Tag: Project   Tag: keep
 ──────────────────────────────────────────────────────────────────────
  i-0f7f6a072d985fd2d   alice   top secret     forever
```

Show output as csv instead of a table (works with any command)

```
ec2 tags -v -o csv
VolumeId,Name,Tags
vol-0439c5ed37f6d455e,awesome-vol,"Name=awesome-vol, Owner=jane"
```

Terminate an instance using its id:

```
ec2 terminate i-06814ad77d5177e5a
```
