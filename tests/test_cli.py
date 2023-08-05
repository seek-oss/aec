from __future__ import annotations

import argparse
from typing import Any

import aec.util.cli as cli
import aec.util.config as config
from aec.util.cli import Arg, Cmd


def test_cli_injects_config():
    def eat(config: dict[str, Any], thing_one: str, temp: str | None = None):
        print(config)
        assert config and isinstance(config, dict) and config["region"]
        assert thing_one == "cheese"
        assert temp == "warm"

    cmds = [Cmd(eat, [Arg("--config"), Arg("thing_one"), Arg("--temp")])]

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.add_command_group(
        subparsers, "food", "food help", cmds, config.inject_config("src/aec/config-example/ec2.toml")
    )

    cli.dispatch(parser, args=["food", "eat", "cheese", "--temp", "warm", "--config", "us"])
    cli.dispatch(parser, args=["food", "eat", "cheese", "--config", "us", "--temp", "warm"])
    cli.dispatch(parser, args=["food", "eat", "--config", "us", "cheese", "--temp", "warm"])
    # When --config isn't supplied, the default profile from the config file is passed in
    cli.dispatch(parser, args=["food", "eat", "cheese", "--temp", "warm"])
