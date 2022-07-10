# Compute Optimizer Usage

Run `aec co -h` for help:

<!-- [[[cog
import cog
from aec.main import build_parser
cog.out(f"```\n{build_parser()._subparsers._actions[1].choices['co'].format_help()}```")
]]] -->
```
usage: aec co [-h] {over-provisioned} ...

optional arguments:
  -h, --help          show this help message and exit

subcommands:
  {over-provisioned}
    over-provisioned  Show recommendations for over-provisioned EC2 instances.
```
<!-- [[[end]]] -->

Show recommendations for over-provisioned instances (eg: idle instances running for more than 30 hours):

```
$ aec co over-provisioned

  ID                    Name         Instance Type   Recommendation   Utilization    Uptime
 ─────────────────────────────────────────────────────────────────────────────────────────────────────
  i-01579de1b005846cb   instance A   m5.4xlarge      r5.2xlarge       CPU MAX 4.0    7 days 8 hours
  i-070c800a592bc6d73   instance B   m5.large        t3.large         CPU MAX 47.0   7 days 8 hours
  i-0ad199cc5b65c621d   instance C   m5.xlarge       r5.large         CPU MAX 30.0   23 days 8 hours
```
