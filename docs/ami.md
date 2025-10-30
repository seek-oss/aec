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
usage: aec ami [-h] {delete,describe,tags,share} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {delete,describe,tags,share}
    delete              Deregister an AMI and delete its snapshot.
    describe            List AMIs.
    tags                List AMI images with their tags.
    share               Share an AMI with another account.
```
<!-- [[[end]]] -->

List images owned by accounts specified in the config file:

<!-- [[[cog
cog.out(f"```\n{docs('aec ami describe', ami.describe(config, owner='099720109477'))}\n```")
]]] -->
```
aec ami describe
                                                                                                    
  Name                             ImageId        CreationDate               RootDeviceName   Size  
 ────────────────────────────────────────────────────────────────────────────────────────────────── 
  ubuntu/images/hvm-ssd/ubuntu-…   ami-1e749f67   2025-10-30T10:58:45.000Z   /dev/sda1        15    
  ubuntu/images/hvm-ssd/ubuntu-…   ami-785db401   2025-10-30T10:58:45.000Z   /dev/sda1        15
```
<!-- [[[end]]] -->

List image by ids

```
aec ami describe ami-1e749f67 ami-785db401
```

List Amazon Deep Learning images:

```
aec ami describe --owner 898082745236
```

List ubuntu focal images owned by Canonical:

```
aec ami describe --owner 099720109477 -q ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64
```

List tags for images

```
aec ami tags 1234567890abcdef1 ami-abcdef12345678901

 ImageId                Name                  Tags
 ────────────────────────────────────────────────────────────────────────────────────
ami-1234567890abcdef1   Best Awesome Ubuntu   Team=Engineering, Source AMI=ami-12345
ami-abcdef12345678901   Best Awesome Linux    Team=Engineering, Source AMI=ami-67890
```
