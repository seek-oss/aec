import json
import os.path
import sys
from typing import Any, Dict

import boto3
import pyjq as pyjq
from argh import arg

from tools.cli import Cli

cli = Cli(config_file="~/.aec/sqs.toml", namespace="sqs", title="sqs commands")


# TODO support multiple queues, via config rather than profile


@arg("file_name", help="file to write messages to")
@arg("--keep", help="keep messages, don't delete them", default=False)
@cli.cmd
def drain(file_name, keep=False, config: Dict[str, Any] = None):
    """Receive messages from the configured queue and write them to a file, pretty print them to stdout and then delete
    them from the queue."""
    queue_url = config["queue_url"]
    printer = config["printer"] if config.get("printer", None) else None

    count = 0

    if os.path.isfile(file_name) and os.path.exists(file_name):
        print(f"{file_name} already exists", file=sys.stderr)
        exit(1)

    sqs_client = boto3.client("sqs", region_name=config["region"])

    with open(file_name, "wb", buffering=0) as o:
        for message in receive_and_delete_messages(sqs_client, queue_url, keep):
            formatted_message = json.dumps(message) + "\n"
            o.write(formatted_message.encode("utf-8", "ignore"))
            if printer:
                print(pyjq.one(printer, message))
            count += 1

    print("Drained " + str(count) + " messages.")


def receive_and_delete_messages(sqs_client, queue_url, keep):
    """
    Receives messages from an SQS queue.

    Note: this continues to receive messages until the queue is empty.
    Every message on the queue will be deleted.

    :param queue_url: URL of the SQS queue to drain.
    :param keep: keep message, don't delete them
    """
    while True:
        resp = sqs_client.receive_message(
            QueueUrl=queue_url, AttributeNames=["All"], MessageAttributeNames=["All"], MaxNumberOfMessages=10,
        )

        try:
            yield from resp["Messages"]
        except KeyError:
            return

        entries = [{"Id": msg["MessageId"], "ReceiptHandle": msg["ReceiptHandle"]} for msg in resp["Messages"]]

        if not keep:
            resp = sqs_client.delete_message_batch(QueueUrl=queue_url, Entries=entries)

            if len(resp["Successful"]) != len(entries):
                raise RuntimeError(f"Failed to delete messages: entries={entries!r} resp={resp!r}")
