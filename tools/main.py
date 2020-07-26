import argh

import tools.configure
import tools.ec2
import tools.sqs


def sort(functions):
    return sorted(functions, key=lambda f: f.__name__)


def main():
    parser = argh.ArghParser()
    for cli in [tools.ec2.cli, tools.sqs.cli]:
        parser.add_commands(
            sorted(cli.commands, key=lambda f: f.__name__),
            namespace=cli.namespace,
            namespace_kwargs=cli.namespace_kwargs,
        )
    parser.add_commands([tools.configure.configure])
    parser.dispatch()


if __name__ == "__main__":
    main()
