# AWS Easy CLI

_"Doesn't do much, easily"_

CLI tools for doing things on AWS easier. Defaults (eg: subnet, tags etc.) only need to be supplied once via a config file, which supports multiple profiles (eg: for different regions or AWS accounts).

Currently supports the following AWS services:

* EC2 - manipulate EC2 instances by name, and launch them with EBS volumes of any size, as per the settings in the configuration file (subnet, tags etc).
* SQS - drain configured SQS queues to a file, pretty printing deleted messages using a jq filter

## Install

1. Ensure you have python version 3.7+ and pip3 installed on your computer
1. Create and switch to a virtualenv if you want to use one ([virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) whilst not required is very useful for creating and switching into virtualenvs).

### Mac

1. Make sure you have automake and libtool installed, eg: `brew install automake libtool` 
1. Run the following to install the latest master version:
   ```
   pip3 install --upgrade git+https://github.com/seek-oss/aec.git
   ```

   (Rerun the same command when you want to upgrade to the latest version)

### Ubuntu

1. Make sure you have automake and libtool installed, eg: `apt install automake libtool python3-pip` 
1. Run the following to install the latest master version:
   ```
   pip3 install --upgrade git+https://github.com/seek-oss/aec.git
   ```

   (Rerun the same command when you want to upgrade to the latest version)

## Configure

1. If your organisation has a config repo, use those instructions to install the config file. If you don't have one, you can install the example config by cloning this repository and running `make install-example-config`.
1. Modify the config files in `~/.aec/` and update any values as needed (eg: `additional_tags`)

## EC2 Usage

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
    drain     Receive messages from the configured queue and write them to a
              file, pretty print them to stdout and then delete them from the
              queue

optional arguments:
  -h, --help  show this help message and exit
```

To drain the queue configured in the `app1` profile to `dlq.txt`, pretty printing the deleted messages:

```
$ sqs drain --profile app1 dlq.txt
822167373.json	RequestId: 393e79a4-cee5-423f-8273-8ea10f1a1fc6 Process exited before completing request
Drained 1 messages.
```

## Similar projects

[awless](https://github.com/wallix/awless) is written in Go, and is an excellent substitute for awscli with support for 
many AWS services. It has human friendly commands for use on the command line or in templates. Unlike `aec` its 
ec2 create instance command doesn't allow you to specify the EBS volume size, or add tags. 
