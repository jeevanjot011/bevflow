# bevflow/aws/sqs.py
import json
import logging
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

LOG = logging.getLogger(__name__)

class MyMessageQueue:
    def __init__(self, region_name=None):
        self.region = region_name or settings.AWS_REGION
        self.sqs = boto3.client('sqs', region_name=self.region)
        self.queue_name = settings.BEVFLOW_ORDER_QUEUE_NAME  # e.g. "bevflow-orders-24231584"

    def create_queue(self):
        try:
            print(f"[SQS] creating queue {self.queue_name}...")
            response = self.sqs.create_queue(QueueName=self.queue_name)
            print(response)
            return True
        except ClientError as e:
            LOG.error(e)
            return False

    def get_queue_url(self):
        # throws if missing
        response = self.sqs.get_queue_url(QueueName=self.queue_name)
        return response['QueueUrl']

    def send_message(self, message_dict):
        try:
            queue_url = self.get_queue_url()
            body = json.dumps(message_dict)
            print(f"[SQS] sending message to {self.queue_name}: {body}")
            self.sqs.send_message(QueueUrl=queue_url, MessageBody=body)
        except ClientError as e:
            LOG.error(e)
            raise

    def delete_queue(self):
        try:
            queue_url = self.get_queue_url()
            self.sqs.delete_queue(QueueUrl=queue_url)
        except ClientError as e:
            LOG.error(e)
            return False
        return True
