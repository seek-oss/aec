# AMI Usage

Run `aec ami -h` for help:

```
usage: aec ami [-h] {delete,describe,share} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {delete,describe,share}
    delete              Deregister an AMI and delete its snapshot.
    describe            List AMIs.
    share               Share an AMI with another account.
```

List images owned by accounts specified in the config file:

```
ami describe
```

List ubuntu focal images owned by Canonical:

```
$ ami describe --owner 099720109477 -q "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64"
Describing images owned by ['099720109477'] with name matching ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64

  Name                                               ImageId                 CreationDate               RootDeviceName
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-07bfe0a3ec9dfcffa   2020-10-14T16:38:23.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-0c43b23f011ba5061   2020-09-25T01:16:05.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-030bb5fda5f7e1896   2020-09-17T16:23:49.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-0dba2cb6798deb6d8   2020-09-08T00:55:25.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-03f6f0014076ab3c5   2020-09-04T22:45:42.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-05cf2c352da0bfb2e   2020-08-18T17:26:37.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-0758470213bdd23b1   2020-07-30T15:39:28.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-06c8ff16263f3db59   2020-07-21T00:35:15.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-0d57c0143330e1fa7   2020-07-16T19:18:04.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-04e7b4117bb0488e4   2020-07-02T03:19:54.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-0c40fbd26b9ac0da9   2020-06-26T16:09:27.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-02ae530dacc099fc9   2020-06-10T01:14:00.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-0e2512bd9da751ea8   2020-05-29T01:38:58.000Z   /dev/sda1
  ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-…   ami-068663a3c619dd892   2020-04-23T11:35:02.000Z   /dev/sda1
```
