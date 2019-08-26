# AWS Swiss Army Knife

CLI tools for doing things on AWS easier. Defaults for your account only need to be supplied once via a config file, which supports multiple profiles (eg: for different regions).

Currently includes:

* EC2 - list images, describe/launch/start/stop/terminate tagged instances with EBS volumes of any size.

## Install

1. `make install` creates and installs the tools into a virtualenv located at `~/.virtualenvs/asak` 
1. Install the example config by running `make install-config` or install your organisation's provided config into `~/.asak/`
1. Modify the config file at `~/.awak/config` and update any values as needed (eg: `additional_tags`)

[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) whilst not required is very useful for switching into asak's virtualenv. 


## EC2 Usage

Activate the virtualenv, eg: `source ~/.virtualenvs/asak/bin/activate` or `workon asak` (if you have virtualenvwrapper installed).

To see the help, run `ec2 -h`

#### Example

To list AMIs created by your account and account 1234 
```
ec2 describe-images  --owners self 1234
```

To launch a t2.medium instance named `lady gaga` with a 100gb EBS volume, and tagged as per the config file's `additional_tags` value:
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


## Similar projects

[awless](https://github.com/wallix/awless) is written in Go, and is an excellent substitute for awscli with support for 
many AWS services. It has human friendly commands for use on the command line or in templates. One limitation is its 
ec2 create instance command doesn't allow you to specify the EBS volume size. 
