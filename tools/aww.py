#!/usr/bin/env python
import sys
from typing import Dict, Any, List, AnyStr

import pytoml as toml
import os.path
import click
from ec2 import ec2

@click.group()
@click.option("--config", help="Config to use", default="default")
@click.pass_context
def aww(ctx, config: str = "default"):
    user_config = load_user_config()
    config = user_config[user_config[config]]
    ctx.obj["config"] = config


def load_user_config() -> Dict[str, Any]:
    filepath = os.path.expanduser('~/.aww/config')
    if not os.path.isfile(filepath):
        print(f"WARNING: No file {filepath}", file=sys.stderr)
        return {}

    with open(filepath) as config_file:
        return toml.load(config_file)

def start():
    ec2(obj={})

if __name__ == "__main__":
    start()