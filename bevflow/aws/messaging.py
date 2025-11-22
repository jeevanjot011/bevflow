import json
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

def get_sqs_url():
    ssm = boto3.client("ssm", region_name=settings.AWS_REGION)
    try:
        resp = ssm.get_parameter(Name=settings.BEVFLOW_SQS_SSM_PARAM)
        return resp["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        # fallback to creating/getting via boto3
        sqs = boto3.client("sqs", region_name=settings.AWS_REGION)
        qname = settings.BEVFLOW_ORDER_QUEUE_NAME
        resp = sqs.create_queue(QueueName=qname)
        return resp["QueueUrl"]

def get_topic_arn():
    ssm = boto3.client("ssm", region_name=settings.AWS_REGION)
    try:
        resp = ssm.get_parameter(Name=settings.BEVFLOW_SNS_SSM_PARAM)
        return resp["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        sns = boto3.client("sns", region_name=settings.AWS_REGION)
        resp = sns.create_topic(Name=settings.BEVFLOW_ORDER_TOPIC_NAME)
        return resp["TopicArn"]

def send_order_to_sqs_and_sns(payload):
    """Idempotent send — uses SSM-stored resources created by bootstrap."""
    sqs = boto3.client("sqs", region_name=settings.AWS_REGION)
    sns = boto3.client("sns", region_name=settings.AWS_REGION)

    queue_url = get_sqs_url()
    # send to SQS
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload))

    # publish short message to SNS for immediate notifications
    topic_arn = get_topic_arn()
    text = f"New order #{payload.get('order_id')} for {payload.get('product_name')} x{payload.get('quantity')} by {payload.get('customer_username')}"
    sns.publish(TopicArn=topic_arn, Message=text)
