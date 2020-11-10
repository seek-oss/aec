# EC2 Usage

Run `aec ec2 -h` for help:

```
usage: aec ec2 [-h] {describe,launch,logs,modify,start,stop,terminate} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {describe,launch,logs,modify,start,stop,terminate}
    describe            List EC2 instances in the region.
    launch              Launch a tagged EC2 instance with an EBS volume.
    logs                Show the system logs.
    modify              Change an instance's type.
    start               Start EC2 instance.
    stop                Stop EC2 instance.
    terminate           Terminate EC2 instance.
```

Launch a t2.medium instance named `lady gaga` with a 50gb EBS volume, with other settings read from the config file:

```
aec ec2 launch "lady gaga" ubuntu1804 --instance-type t2.medium --volume-size 50
```

Stop the instance:

```
aec ec2 stop "lady gaga"
```

Modify the instance type:

```
aec ec2 modify "lady gaga" p2.xlarge
```

List instances containing `gaga` in the name:

```
aec ec2 describe -q gaga
```

By default, commands will use the default profile as specified in the config file. To list ec2 instances using the non-default config `us`:

```
aec ec2 describe --config us

  State     Name         Type          DnsName            LaunchTime         ImageId            InstanceId  
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  running   instance A   t2.micro      ec2-34-222-181-…   2020-08-31         ami-042e958219c…   i-0547be212903d…  
                                                                22:33:29+00:00  
  running   instance B   m5.large      ip-10-17-26-251…   2020-10-18         ami-0e40c8f9700…   i-0e0ea2dc778d7…  
                                                                11:05:07+00:00  
  stopped   instance C   t2.nano       ip-10-17-26-180…   2020-10-22         ami-0d5f76fa1b9…   i-0882dcea73a85…  
                                                                19:29:14+00:00  
```

Show running or pending instances only:

```
ec2 describe -r
```

Terminate an instance using its id:

```
ec2 terminate i-06814ad77d5177e5a
```
