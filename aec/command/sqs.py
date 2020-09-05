import json
import os.path
import sys
from typing import Any, Dict, Iterator

import boto3
import pyjq as pyjq
from mypy_boto3_sqs.client import SQSClient
from mypy_boto3_sqs.type_defs import MessageTypeDef

# TODO support multiple queues, via config rather than profile


def drain(config: Dict[str, Any], file_name: str, keep: bool = False) -> None:
    """Receive messages from the configured queue and write them to a file, pretty print them to stdout and then delete
    them from the queue."""
    queue_url = config["queue_url"]
    printer = config["printer"] if config.get("printer", None) else None

    count = 0

    if os.path.isfile(file_name) and os.path.exists(file_name):
        print(f"{file_name} already exists", file=sys.stderr)
        exit(1)

    sqs_client = boto3.client("sqs", region_name=config.get("region", None))

    with open(file_name, "wb", buffering=0) as o:
        for message in receive_and_delete_messages(sqs_client, queue_url, keep):
            formatted_message = json.dumps(message) + "\n"
            o.write(formatted_message.encode("utf-8", "ignore"))
            if printer:
                print(pyjq.one(printer, message))
            count += 1

    print("Drained " + str(count) + " messages.")


def receive_and_delete_messages(sqs_client: SQSClient, queue_url: str, keep: bool) -> Iterator[MessageTypeDef]:
    """
    Receives and yields messages from an SQS queue, before deleting them.

    Note: this continues to receive messages until the queue is empty.
    Every message on the queue will be deleted.

    :param sqs_client: boto3 SQS client
    :param queue_url: URL of the SQS queue to drain.
    :param keep: keep message, don't delete them

    :raises RuntimeError: if messages cannot be deleted
    :yield: messages
    """
    while True:
        resp = sqs_client.receive_message(
            QueueUrl=queue_url,
            AttributeNames=["All"],
            MessageAttributeNames=["All"],
            MaxNumberOfMessages=10,
        )

        try:
            yield from resp["Messages"]
        except KeyError:
            return

        entries = [{"Id": msg["MessageId"], "ReceiptHandle": msg["ReceiptHandle"]} for msg in resp["Messages"]]

        if not keep:
            resp = sqs_client.delete_message_batch(QueueUrl=queue_url, Entries=entries)  # type: ignore see https://github.com/microsoft/pyright/issues/1008

            if len(resp["Successful"]) != len(entries):
                raise RuntimeError(f"Failed to delete messages: entries={entries!r} resp={resp!r}")
