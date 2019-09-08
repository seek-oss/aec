import sys
from os import path

import argh
import boto3
import pyjq as pyjq

from tools.cli import *

cli = Cli(config_file='~/.aec/sqs.toml').cli

@arg('file_name', help="file to write messages to")
@arg('--keep', help="keep messages, don't delete them", default=False)
@cli
def drain(config, file_name, keep=False):
    """
    Drains messages from a queue and writes them to a file
    """
    queue_url = config['queue_url']
    printer = config['printer'] if config.get('printer', None) else None

    count = 0

    if path.isfile(file_name) and path.exists(file_name):
        print(f'{file_name} already exists', file=sys.stderr)
        exit(1)

    with open(file_name, 'wb', buffering=0) as o:
        for message in receive_and_delete_messages(queue_url, keep):
            formatted_message = json.dumps(message) + "\n"
            o.write(formatted_message.encode('utf-8', 'ignore'))
            if printer:
                print(pyjq.one(printer, message))
            count += 1

    print("Drained " + str(count) + " messages.")


def receive_and_delete_messages(queue_url, keep):
    """
    Receives messages from an SQS queue.

    Note: this continues to receive messages until the queue is empty.
    Every message on the queue will be deleted.

    :param queue_url: URL of the SQS queue to drain.
    :param keep: keep message, don't delete them

    """
    sqs_client = boto3.client('sqs')

    while True:
        resp = sqs_client.receive_message(
            QueueUrl=queue_url,
            AttributeNames=['All'],
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=10
        )

        try:
            yield from resp['Messages']
        except KeyError:
            return

        entries = [
            {'Id': msg['MessageId'], 'ReceiptHandle': msg['ReceiptHandle']}
            for msg in resp['Messages']
        ]

        if not keep:
            resp = sqs_client.delete_message_batch(
                QueueUrl=queue_url, Entries=entries
            )

            if len(resp['Successful']) != len(entries):
                raise RuntimeError(
                    f"Failed to delete messages: entries={entries!r} resp={resp!r}"
                )


def main():
    parser = argh.ArghParser()
    parser.add_commands([drain])
    parser.dispatch()


if __name__ == '__main__':
    main()
