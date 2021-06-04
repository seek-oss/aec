# SSM Usage

Run `aec ssm -h` for help:

```
usage: aec ssm [-h] {describe} ...

optional arguments:
  -h, --help  show this help message and exit

subcommands:
  {describe}
    describe  Describe instances running the SSM agent.
```

Describe:

```
aec ssm describe

  ID                    Name                   PingStatus   Platform         AgentVersion
 ─────────────────────────────────────────────────────────────────────────────────────────
  i-01579de1b005846cb   awesome-instance       Online       Amazon Linux 2   2.3.1319.0
  i-0f194c8d697f35240   even-better-instance   Online       Ubuntu 20.04     2.3.978.0
```

Run hello world on instances:

```
echo 'echo Hello World' | ssm run awesome-instance i-0f194c8d697f35240 
```
