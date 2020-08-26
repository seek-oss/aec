# Compute Optimizer Usage

To see the help, run `aec co -h`

```
usage: aec co [-h] {over-provisioned} ...

optional arguments:
  -h, --help          show this help message and exit

subcommands:
  {over-provisioned}
    over-provisioned  Show recommendations for over-provisioned EC2 instances.
```

To show recommendations for over-provisioned instanctes:

```
$ aec co over-provisioned

  ID                    Name                                            Instance Type   Recommendation
 ──────────────────────────────────────────────────────────────────────────────────────────────────────
  i-01579de1b005846cb   instance A                                       m5.4xlarge      r5.2xlarge
  i-070c800a592bc6d73   instance B                                       m5.xlarge       r5.large
  i-0ad199cc5b65c621d   instance C                                       m5.xlarge       t3.xlarge
```
