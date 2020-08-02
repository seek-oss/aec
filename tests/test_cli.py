from typing import Any, Dict, Optional

import argh

from tools.cli import Cli


def test_cli_injects_config():

    # config is given a default value because it is an optional cli arg.
    # When --config isn't supplied, the default profile from the config
    # file is passed in
    def eat(thing, temp: Optional[str] = None, config: Dict[str, Any] = None):
        print(config)
        assert config and isinstance(config, dict) and config["region"] == "us-east-1"
        assert thing == "cheese"
        assert temp == "warm"

    cli = Cli(config_file="tools/config-example/ec2.toml", namespace="test")

    cli.cmd(eat)

    parser = argh.ArghParser()
    parser.add_commands(cli.commands)
    parser.dispatch(argv=["eat", "cheese", "--temp", "warm", "--config", "us"])
    parser.dispatch(argv=["eat", "cheese", "--config", "us", "--temp", "warm"])
    parser.dispatch(argv=["eat", "--config", "us", "cheese", "--temp", "warm"])


def test_cli_pretty_prints_list_as_table():
    def listy(config: Dict[str, Any] = None):
        return [{"a": 1, "b": 2}]

    cli = Cli(config_file="tools/config-example/ec2.toml", namespace="test")

    cli.cmd(listy)

    parser = argh.ArghParser()
    parser.add_commands(cli.commands)
    output = parser.dispatch(argv=["listy"], output_file=None)

    assert output == f"a  b  \n1  2  \n"
