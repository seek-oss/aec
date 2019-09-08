# AWS Easy CLI

_"Doesn't do much, easily"_

CLI tools for doing things on AWS easier. Defaults (eg: subnet, tags etc.) only need to be supplied once via a config file, which supports multiple profiles (eg: for different regions or AWS accounts).

Currently supports the following AWS services:

* EC2 - manipulate EC2 instances by name, and launch them with EBS volumes of any size, as per the settings in the configuration file (subnet, tags etc).

## Install

1. Run `make install` to create and install the tools into a virtualenv located at `~/.virtualenvs/aec` 
1. If your organisation has a config repo, use those instructions to install the config file. If you don't have one, you can install the example config by running `make install-config`.
1. Modify the config files in `~/.aec/` and update any values as needed (eg: `additional_tags`)

[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) whilst not required is very useful for switching into the aec virtualenv. 


## EC2 Usage

Activate the virtualenv, eg: `source ~/.virtualenvs/aec/bin/activate` or `workon aec` (if you have virtualenvwrapper installed).

To see the help, run `ec2 -h`
```
usage: ec2 [-h]
           {delete-image,describe,describe-images,launch,modify,share-image,start,stop,terminate}
           ...

positional arguments:
  {delete-image,describe,describe-images,launch,modify,share-image,start,stop,terminate}
    delete-image        Deregisters an AMI and deletes its snapshot
    describe            List EC2 instances in the region
    describe-images     List AMIs
    launch              Launch a tagged EC2 instance with an EBS volume
    modify              Change an instance's type
    share-image         Share an AMI with another account
    start               Start EC2 instances by name
    stop                Stop EC2 instances by name
    terminate           Terminate EC2 instances by name

optional arguments:
  -h, --help            show this help message and exit
```

#### Examples

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

By default, commands will use the default profile as specified in the config file. To list ec2 instances using the non-default profile `us`
```
ec2 describe --profile us  
```

## SQS Usage

Activate the virtualenv, eg: `source ~/.virtualenvs/aec/bin/activate` or `workon aec` (if you have virtualenvwrapper installed).

To see the help, run `sqs -h`

```
usage: sqs [-h] {drain} ...

positional arguments:
  {drain}
    drain     Drains messages from a queue and writes them to a file

optional arguments:
  -h, --help  show this help message and exit
```

## Similar projects

[awless](https://github.com/wallix/awless) is written in Go, and is an excellent substitute for awscli with support for 
many AWS services. It has human friendly commands for use on the command line or in templates. Unlike `aec` its 
ec2 create instance command doesn't allow you to specify the EBS volume size, or add tags. 
