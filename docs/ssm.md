# AWS Systems Manager (SSM) Usage

Run `aec ssm -h` for help:

<!-- [[[cog
import cog
from aec.main import build_parser
cog.out(f"```\n{build_parser()._subparsers._actions[1].choices['ssm'].format_help()}```")
]]] -->
```
usage: aec ssm [-h] {commands,compliance-summary,describe,invocations,output,patch,patch-summary,run} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {commands,compliance-summary,describe,invocations,output,patch,patch-summary,run}
    commands            List commands by instance.
    compliance-summary  Compliance summary for instances that have run the patch baseline.
    describe            List running instances with the SSM agent.
    invocations         List invocations of a command across instances.
    output              Fetch output of a command from S3.
    patch               Scan or install AWS patch baseline.
    patch-summary       Patch summary for all instances that have run the patch baseline.
    run                 Run a shell script on instance(s). Script is read from stdin.
```
<!-- [[[end]]] -->

## Examples

List running instances with the SSM agent.

```
aec ssm describe

  ID                    Name                   PingStatus   Platform         AgentVersion
 ─────────────────────────────────────────────────────────────────────────────────────────
  i-01579de1b005846cb   awesome-instance       Online       Amazon Linux 2   2.3.1319.0
  i-0f194c8d697f35240   even-better-instance   Online       Ubuntu 20.04     2.3.978.0
```

List running instances containing `gaga` in the name:

```
aec ssm describe -q gaga
```

Run a hello world command on multiple instances:

```
echo 'echo Hello World' | aec ssm run awesome-instance i-0f194c8d697f35240
```

Fetch stdout of the hello world command for the invocation on i-0f194c8d697f35240 (requires S3 bucket [configuration](##Config)):

```
aec ssm output 3dd3482e-20f2-4a4a-a9f6-0989a0d38ced i-0f194c8d697f35240
```

List all commands

```
aec ssm commands
  RequestedDateTime   CommandId                              Status     DocumentName           Operation   # target   # error   # timeout   # complete
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  2022-08-27 15:10    6dc4699b-f9f2-43b5-8d46-314eaf11b8dc   Failed     AWS-RunPatchBaseline   Install     60         3                     60
  2022-08-26 22:15    3f12a15e-9149-4f55-a4ad-998fc8f731bb   Success    AWS-RunPatchBaseline   Scan        1                                1
```

Invocations of a command

```
aec ssm invocations 6dc4699b-f9f2-43b5-8d46-314eaf11b8dc
```

Invocations of a command, with output formatted using [xsv](https://github.com/BurntSushi/xsv) so ConsoleLink is visible:

```
aec ssm invocations 6dc4699b-f9f2-43b5-8d46-314eaf11b8dc -o csv | xsv select Name,StatusDetails,ConsoleLink | xsv table
```

Patch summary for all instances (that have run the patch baseline):

```
aec ssm patch-summary
  InstanceId            Name                            Needed   Pending Reboot   Errored   Rejected   Last operation time         Last operation
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  i-01579de1b005846cb   awesome-instance                                                               2021-06-04 23:13:56+10:00   Scan
  i-0f194c8d697f35240   even-better-instance            22                                             2021-01-22 06:02:44+11:00   Install
```

Compliance status of running instances (that have run the patch baseline):

```
aec ssm compliance-summary

  InstanceId            Name                    Status          NonCompliantCount   Last operation time
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  i-01579de1b005846cb   awesome-instance        COMPLIANT                           2021-06-05 22:08:26+10:00
  i-0f194c8d697f35240   even-better-instance    NON_COMPLIANT   22                  2021-06-05 22:11:53+10:00
```

Patch an instance but don't reboot:

```
aec ssm patch install awesome-instance --no-reboot
```

NB: if an instance is patched with the NoReboot option, and there are patches pending a reboot, then the instance will have a non-compliant status. Reboot the instance and run the patch baseline scan to update its patch status to compliant.

Run the scan and update patch/compliance status:

```
aec ssm patch scan awesome-instance
```

## Config

[_ec2.toml_](../src/aec/config-example/ec2.toml):

```
[profile.ssm]
s3bucket = "logs"
s3prefix = "ssm-command"
```

_s3bucket_ and _s3prefix_ are optional. They will be used as the location to store the output of `run` and `patch` commands.
