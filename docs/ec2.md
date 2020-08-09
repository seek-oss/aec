# EC2 Usage

To see the help, run `aec ec2 -h`

```
usage: aec ec2 [-h] {delete-image,describe,describe-images,launch,modify,share-image,start,stop,terminate} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {delete-image,describe,describe-images,launch,modify,share-image,start,stop,terminate}
    delete-image        Deregister an AMI and delete its snapshot.
    describe            List EC2 instances in the region.
    describe-images     List AMIs.
    launch              Launch a tagged EC2 instance with an EBS volume.
    modify              Change an instance's type.
    share-image         Share an AMI with another account.
    start               Start EC2 instances by name.
    stop                Stop EC2 instances by name.
    terminate           Terminate EC2 instances by name.
```

To list AMIs (owned by accounts specified in the config file)

```
ec2 describe-images
```

To launch a t2.medium instance named `lady gaga` with a 100gb EBS volume, with other settings read from the config file

```
ec2 launch "lady gaga" ami-0bfe6b818fce462af --instance-type t2.medium --volume-size 100  
```

Stop the instance

```
ec2 stop "lady gaga"
```

By default, commands will use the default profile as specified in the config file. To list ec2 instances using the non-default config `us`

```
ec2 describe --config us  
```
