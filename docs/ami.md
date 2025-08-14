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
  ubuntu/images/hvm-ssd/ubuntu-…   ami-1e749f67   2025-08-14T10:56:57.000Z   /dev/sda1        15    
  ubuntu/images/hvm-ssd/ubuntu-…   ami-785db401   2025-08-14T10:56:57.000Z   /dev/sda1        15
```
<!-- [[[end]]] -->

List image by id

```
aec ami describe ami-025b9fd66d61d093a
```

List Amazon Deep Learning images:

```
aec ami describe --owner 898082745236
```

List ubuntu focal images owned by Canonical:

```
aec ami describe --owner 099720109477 -q ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64
```

List tags for image

```
aec ami tags ami-1234567890abcef12

 ImageId                Name                  Tags
 ────────────────────────────────────────────────────────────────────────────────────
ami-1234567890abcef12   Best Awesome Ubuntu   Team=Engineering, Source AMI=ami-12345
```
