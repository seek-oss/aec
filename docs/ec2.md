# EC2 Usage

To see the help, run `aec ec2 -h`

```
usage: aec ec2 [-h]
               {delete-image,describe,describe-images,launch,logs,modify,share-image,start,stop,terminate}
               ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {delete-image,describe,describe-images,launch,logs,modify,share-image,start,stop,terminate}
    delete-image        Deregister an AMI and delete its snapshot.
    describe            List EC2 instances in the region.
    describe-images     List AMIs.
    launch              Launch a tagged EC2 instance with an EBS volume.
    logs                Show the system logs.
    modify              Change an instance's type.
    share-image         Share an AMI with another account.
    start               Start EC2 instances by name.
    stop                Stop EC2 instances by name.
    terminate           Terminate EC2 instances by name.
```

To list AMIs (owned by accounts specified in the config file)

```
aec ec2 describe-images
```

To launch a t2.medium instance named `lady gaga` with a 50gb EBS volume, with other settings read from the config file

```
aec ec2 launch "lady gaga" ubuntu1804 --instance-type t2.medium --volume-size 50
```

Stop the instance

```
aec ec2 stop "lady gaga"
```

By default, commands will use the default profile as specified in the config file. To list ec2 instances using the non-default config `us`

```
aec ec2 describe --config us
```
