# AWS Easy CLI

_"Doesn't do much, easily"_.

CLI tools for doing things on AWS easier. Defaults (eg: subnet, tags etc.) only need to be supplied once via a config file, which supports multiple profiles (eg: for different regions or AWS accounts).

Currently supports the following AWS services:

* [EC2](docs/ec2.md) - manipulate EC2 instances by name, and launch them with EBS volumes of any size, as per the settings in the configuration file (subnet, tags etc).
* [SQS](docs/sqs.md) - drain configured SQS queues to a file, pretty printing deleted messages using a jq filter

## Prerequisites

* python 3.7+
* pip3
* automake & libtool:  
  * Ubuntu: `sudo apt install automake libtool`
  * macOS: `brew install automake libtool`

## Install

Run the following to install the latest master version using [pipx](https://github.com/pipxproject/pipx):

```
pipx install git+https://github.com/seek-oss/aec.git
```

If you have previously installed aec, run `pipx upgrade aec` to upgrade to the latest version.

## Configure

Before you can use aec, you will need to create the config files in `~/.aec/`. The config files contain settings for your AWS account including VPC details and additional tagging requirements.

To get started, run `aec configure example` to install the [example config files](tools/config-example/) and then update them as needed.

## Handy aliases

For even faster access to aec subcommands, you may like to add the following aliases to your .bashrc:

```
alias ec2='aec ec2'
alias sqs='aec sqs'
```

## Development

Pre-reqs:
* make
* [pre-commit](https://pre-commit.com/)
* node (required for pyright)

To get started run `make install`. This will:
* install git hooks for formatting & linting on git push
* create the virtualenv
* install this package in editable mode

Then run `make` to see the options for running checks, tests etc.

## Similar projects

[awless](https://github.com/wallix/awless) is written in Go, and is an excellent substitute for awscli with
support for many AWS services. It has human friendly commands for use on the command line or in templates. Unlike `aec` its ec2 create instance command doesn't allow you to specify the EBS volume size, or add tags.
