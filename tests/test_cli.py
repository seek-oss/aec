import argparse
from typing import Any, Dict, Optional

import tools.cli as cli
from tools.cli import Arg, Cmd


def test_cli_injects_config():
    def eat(config: Dict[str, Any], thing, temp: Optional[str] = None):
        print(config)
        assert config and isinstance(config, dict) and config["region"]
        assert thing == "cheese"
        assert temp == "warm"

    cmds = [Cmd("eat", eat, [Arg("--config"), Arg("thing"), Arg("--temp")])]

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.add_command_group(subparsers, "food", "food help", cmds, cli.inject_config("tools/config-example/ec2.toml"))

    cli.dispatch(parser, args=["food", "eat", "cheese", "--temp", "warm", "--config", "us"])
    cli.dispatch(parser, args=["food", "eat", "cheese", "--config", "us", "--temp", "warm"])
    cli.dispatch(parser, args=["food", "eat", "--config", "us", "cheese", "--temp", "warm"])
    # When --config isn't supplied, the default profile from the config file is passed in
    cli.dispatch(parser, args=["food", "eat", "cheese", "--temp", "warm"])
