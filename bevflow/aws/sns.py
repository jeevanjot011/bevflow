# bevflow/aws/sns.py
import logging
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

LOG = logging.getLogger(__name__)

class Publisher:
    def __init__(self, region_name=None):
        self.region = region_name or settings.AWS_REGION
        self.sns = boto3.client('sns', region_name=self.region)
        self.topic_name = settings.BEVFLOW_ORDER_TOPIC_NAME  # e.g. "bevflow-orders-topic-24231584"

    def create_topic(self):
        try:
            print(f"[SNS] creating/getting topic {self.topic_name}")
            response = self.sns.create_topic(Name=self.topic_name)
            return response['TopicArn']
        except ClientError as e:
            LOG.error(e)
            raise

    def publish_message(self, message_text):
        try:
            topic_arn = self.create_topic()
            print(f"[SNS] publishing to {topic_arn}: {message_text}")
            self.sns.publish(TopicArn=topic_arn, Message=message_text)
            return True
        except ClientError as e:
            LOG.error(e)
            return False

    def subscribe_email(self, email_address):
        """
        Subscribe an email (manufacturer) to the topic (requires confirm).
        """
        try:
            topic_arn = self.create_topic()
            self.sns.subscribe(TopicArn=topic_arn, Protocol='email', Endpoint=email_address)
            return True
        except ClientError as e:
            LOG.error(e)
            return False

    def subscribe_sqs_queue(self, queue_arn):
        try:
            topic_arn = self.create_topic()
            print(f"[SNS] subscribing SQS {queue_arn} to {topic_arn}")
            self.sns.subscribe(TopicArn=topic_arn, Protocol='sqs', Endpoint=queue_arn)
            return True
        except ClientError as e:
            LOG.error(e)
            return False
