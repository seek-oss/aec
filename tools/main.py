import argh

import tools.ec2
import tools.sqs


def sort(functions):
    return sorted(functions, key=lambda f: f.__name__)


def main():
    parser = argh.ArghParser()
    parser.add_commands(sort(tools.ec2.cli.commands), namespace=tools.ec2.cli.namespace)
    parser.add_commands(sort(tools.sqs.cli.commands), namespace=tools.sqs.cli.namespace)
    parser.dispatch()


if __name__ == "__main__":
    main()
