# SSM Usage

To see the help, run `aec ssm -h`

```
usage: aec ssm [-h] {describe} ...

optional arguments:
  -h, --help  show this help message and exit

subcommands:
  {describe}
    describe  Describe instances running the SSM agent.
```

Example:

```
$ aec ssm describe

  ID                    Name                   PingStatus   Platform         AgentVersion
 ─────────────────────────────────────────────────────────────────────────────────────────
  i-01579de1b005846cb   awesome-instance       Online       Amazon Linux 2   2.3.1319.0
  i-0f194c8d697f35240   even-better-instance   Online       Ubuntu 20.04     2.3.978.0
```
