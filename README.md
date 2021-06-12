# AWS EC2 CLI

[![Build](https://github.com/seek-oss/aec/actions/workflows/pythonapp.yml/badge.svg)](https://github.com/seek-oss/aec/actions/workflows/pythonapp.yml)
[![PyPI version](https://badge.fury.io/py/aec-cli.svg)](https://pypi.org/project/aec-cli/)

_"Instead of using the console, use the cli!"_.

Command-line tools for managing pet EC2 instances by name.

Defaults only need to be supplied once via a [config file](src/aec/config-example/ec2.toml), which supports multiple profiles for different regions or AWS accounts.

For examples see:

- [EC2](docs/ec2.md) - manipulate EC2 instances by name, and launch them with tags and EBS volumes of any size, as per the settings in the configuration file (subnet, security group etc).
- [AMI](docs/ami.md) - describe, delete and share images
- [Compute Optimizer](docs/compute-optimizer.md) - show over-provisioned instances
- [SSM](docs/ssm.md) - run commands on instances, and [ssm patch management](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-patch.html)

## Prerequisites

- python 3.7+
  - Ubuntu 20.04: `sudo apt install python3 python3-pip python3-dev python3-venv`
- automake:
  - Ubuntu: `sudo apt install automake`
  - macOS: `brew install automake`

## Install

Run the following to install the latest master version using pip:

```
pip install aec-cli
```

If you have previously installed aec, run the following to upgrade to the latest version:

```
pip install --upgrade aec-cli
```

NB: Consider using [pipx](https://github.com/pipxproject/pipx) to install aec-cli into its own isolated virtualenv.

## Configure

Before you can use aec, you will need to create the config files in `~/.aec/`. The config files contain settings for your AWS account including VPC details and additional tagging requirements.

To get started, run `aec configure example` to install the [example config files](src/aec/config-example/) and then update them as needed.

## Handy aliases

For even faster access to aec subcommands, you may like to add the following aliases to your .bashrc:

```
alias ec2='COLUMNS=$COLUMNS aec ec2'
alias ami='COLUMNS=$COLUMNS aec ami'
alias ssm='COLUMNS=$COLUMNS aec ssm'
```

`COLUMNS=$COLUMNS` will ensure output is formatted to the width of your terminal when piped.

## FAQ

### How do I use aec with other AWS profiles?

To use aec with the named profile 'production':

```
export AWS_DEFAULT_PROFILE=production
aec ec2 describe
```

## Development

Pre-reqs:

- make
- node (required for pyright)

To get started run `make install`. This will:

- install git hooks for formatting & linting on git push
- create the virtualenv
- install this package in editable mode

Then run `make` to see the options for running checks, tests etc.

## Similar projects

[wallix/awless](https://github.com/wallix/awless) is written in Go, and is an excellent substitute for awscli with
support for many AWS services. It has human friendly commands for use on the command line or in templates. Unlike `aec` its ec2 create instance command doesn't allow you to specify the EBS volume size, or add tags.

[achiku/jungle](https://github.com/achiku/jungle) is written in Python, and incorporates a smaller subset of ec2 commands and doesn't launch new instances. It does however have an ec2 ssh command. It also supports other AWS services like ELB, EMR, RDS.
