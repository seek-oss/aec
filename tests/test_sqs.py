import boto3
import pytest
from moto import mock_sqs

from aec.sqs import drain


@pytest.fixture
def mock_aws_configs():
    mock = mock_sqs()
    mock.start()

    region = "ap-southeast-2"
    sqs = boto3.resource("sqs", region_name=region)

    # pylint: disable=maybe-no-member
    queue = sqs.create_queue(QueueName="test-queue")

    queue.send_message(
        MessageBody="""{
            "Records": [{
                "Sns": {
                    "Message": "{\\"Records\\":[{\\"eventVersion\\":\\"2.1\\",\\"eventSource\\":\\"aws:s3\\",\\"awsRegion\\":\\"ap-southeast-2\\",\\"eventTime\\":\\"2019-09-03T14:38:13.181Z\\",\\"eventName\\":\\"ObjectCreated:Put\\",\\"userIdentity\\":{\\"principalId\\":\\"AWS:AROAJ2EX5FOYCOFZZBQMI:projector\\"},\\"requestParameters\\":{\\"sourceIPAddress\\":\\"13.239.35.38\\"},\\"responseElements\\":{\\"x-amz-request-id\\":\\"180C8AB8E33CF7EA\\",\\"x-amz-id-2\\":\\"FhU4Sb2ZhYiSEW+5MKqUU+EYax31OZS8Lf6AtbIOMSyuWeknhTNMHzCTF8QbWCSe8/84tWqH+JM=\\"},\\"s3\\":{\\"s3SchemaVersion\\":\\"1.0\\",\\"configurationId\\":\\"27b8c781-fe54-42e9-8f68-49ae10a62845\\",\\"bucket\\":{\\"name\\":\\"seek-apply-projections-prod\\",\\"ownerIdentity\\":{\\"principalId\\":\\"AVJWBGAX8UAFM\\"},\\"arn\\":\\"arn:aws:s3:::my-app-bucket\\"},\\"object\\":{\\"key\\":\\"822167373.json\\",\\"size\\":6039,\\"eTag\\":\\"1b8938b6028c1bceb39fb0ad4d2c3b26\\",\\"versionId\\":\\"tZW5WAAtsYSmcu1DA0tDX5r_LPrPxcEg\\",\\"sequencer\\":\\"005D6E7AD523036FB8\\"}}}]}"
                }
            }]
        }""",
        MessageAttributes={
            "ErrorMessage": {
                "StringValue": "RequestId: 393e79a4-cee5-423f-8273-8ea10f1a1fc6 Process exited before completing request",
                "DataType": "String",
            }
        },
    )

    return {
        "region": region,
        "queue_url": queue.url,
        "printer": "[(.Body | fromjson | .Records[].Sns.Message | fromjson | .Records[].s3.object.key), .MessageAttributes.ErrorMessage.StringValue] | @tsv",
    }


def test_drain(mock_aws_configs):
    drain(mock_aws_configs, "/dev/null")
    assert approximate_messages_not_visible(mock_aws_configs) == 0


def test_drain_keep(mock_aws_configs):
    drain(mock_aws_configs, "/dev/null", keep=True)
    assert approximate_messages_not_visible(mock_aws_configs) == 1


def approximate_messages_not_visible(config) -> int:
    sqs_client = boto3.client("sqs", region_name=config["region"])
    resp = sqs_client.get_queue_attributes(
        QueueUrl=config["queue_url"], AttributeNames=["ApproximateNumberOfMessagesNotVisible"],
    )
    print(resp)
    return int(resp["Attributes"]["ApproximateNumberOfMessagesNotVisible"])
