<!-- [[[cog
import cog
from aec.util.docgen import docs
from aec.util.docgen import mock_aws_config as config
import aec.command.ami as ami
]]] -->
<!-- [[[end]]] -->

# AMI Usage

Run `aec ami -h` for help:

<!-- [[[cog
from aec.main import build_parser
cog.out(f"```\n{build_parser()._subparsers._actions[1].choices['ami'].format_help()}```")
]]] -->
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
<!-- [[[end]]] -->

List images owned by accounts specified in the config file:

<!-- [[[cog
cog.out(f"```\n{docs('aec ami describe', ami.describe(config, owner='099720109477'))}\n```")
]]] -->
```
aec ami describe
                                                                                                                                     
  Name                                                              ImageId        CreationDate               RootDeviceName   Size  
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-20170727   ami-1e749f67   2022-11-15T04:12:25.000Z   /dev/sda1        15    
  ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20170721   ami-785db401   2022-11-15T04:12:25.000Z   /dev/sda1        15
```
<!-- [[[end]]] -->

List image by id

```
ami describe ami-025b9fd66d61d093a
```

List Amazon Deep Learning images:

```
ami describe --owner 898082745236
```

List ubuntu focal images owned by Canonical:

```
aec ami describe --owner 099720109477 -q ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64
```
