# bevflow/aws/bootstrap.py
import os
import json
import time
import zipfile
import tempfile
import shutil
import subprocess
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

ssm = boto3.client("ssm", region_name=settings.AWS_REGION)
s3 = boto3.client("s3", region_name=settings.AWS_REGION)
sqs = boto3.client("sqs", region_name=settings.AWS_REGION)
sns = boto3.client("sns", region_name=settings.AWS_REGION)
lambda_client = boto3.client("lambda", region_name=settings.AWS_REGION)
iam = boto3.client("iam", region_name=settings.AWS_REGION)
dynamodb = boto3.client("dynamodb", region_name=settings.AWS_REGION)

def ssm_put(name, value):
    ssm.put_parameter(Name=name, Value=value, Type="String", Overwrite=True)

def ensure_sqs():
    qname = settings.BEVFLOW_ORDER_QUEUE_NAME
    try:
        resp = sqs.get_queue_url(QueueName=qname)
        return resp["QueueUrl"]
    except ClientError:
        resp = sqs.create_queue(QueueName=qname)
        return resp["QueueUrl"]

def ensure_sns():
    tname = settings.BEVFLOW_ORDER_TOPIC_NAME
    resp = sns.create_topic(Name=tname)
    return resp["TopicArn"]

def subscribe_sqs_to_sns(topic_arn, queue_url):
    # Get queue ARN
    attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
    queue_arn = attrs["Attributes"]["QueueArn"]
    # Subscribe SQS to topic
    # Avoid duplicate subscribe: list subscriptions for topic
    subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn).get("Subscriptions", [])
    for s in subs:
        if s.get("Endpoint") == queue_arn:
            return True
    sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=queue_arn)
    # Add permission to allow SNS to send to SQS
    policy = {
        "Version": "2012-10-17",
        "Id": f"{queue_arn}/SQSDefaultPolicy",
        "Statement": [{
            "Sid": "Allow-SNS-SendMessage",
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": "SQS:SendMessage",
            "Resource": queue_arn,
            "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}}
        }]
    }
    sqs.set_queue_attributes(
        QueueUrl=queue_url,
        Attributes={"Policy": json.dumps(policy)}
    )
    return True

def ensure_dynamodb_table():
    table_name = settings.BEVFLOW_DDB_TABLE
    existing = dynamodb.list_tables().get("TableNames", [])
    if table_name not in existing:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "order_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "order_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        # wait until exists
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 2, "MaxAttempts": 10})
    return table_name

def ensure_logs_bucket():
    # use existing bucket logic from your s3 module or simple name based on env id
    bucket_param = settings.BEVFLOW_LOGS_BUCKET_PARAM
    try:
        resp = ssm.get_parameter(Name=bucket_param)
        return resp["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        # create a logs bucket name
        bucket_name = f"bevflow-logs-{settings.AWS_ENV_ID}-{int(time.time())}"
        if settings.AWS_REGION == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION})
        ssm.put_parameter(Name=bucket_param, Value=bucket_name, Type="String", Overwrite=True)
        return bucket_name

def package_lambda():
    """
    Create ZIP containing lambda code and dependencies (dublininstance).
    This installs requirements into a temp folder and zips them with the handler file.
    """
    # paths
    base = os.path.dirname(os.path.abspath(__file__))  # bevflow/aws
    lambda_dir = os.path.join(base, "lambda")
    handler_file = os.path.join(lambda_dir, "order_processor.py")
    req_file = os.path.join(lambda_dir, "requirements.txt")

    tempdir = tempfile.mkdtemp()
    try:
        # pip install dependencies into tempdir/python
        site_packages = os.path.join(tempdir, "python")
        os.makedirs(site_packages, exist_ok=True)
        # install dependencies
        subprocess.check_call([
            "pip", "install", "-r", req_file, "-t", site_packages
        ])
        # copy handler file into tempdir
        shutil.copy(handler_file, tempdir)

        # zip everything in tempdir (handler at root)
        zip_path = os.path.join(tempdir, "lambda_package.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # add site-packages content
            for root, dirs, files in os.walk(site_packages):
                for f in files:
                    full = os.path.join(root, f)
                    arcname = os.path.relpath(full, site_packages)
                    zf.write(full, arcname)
            # add handler
            zf.write(os.path.join(tempdir, "order_processor.py"), "order_processor.py")
        return zip_path
    finally:
        # don't delete tempdir here (Lambda upload reads it); we will clean up later if needed
        pass

def ensure_lambda(lambda_zip_path, role_arn, topic_arn, queue_url, logs_bucket):
    func_name = settings.BEVFLOW_LAMBDA_NAME
    # create or update function
    try:
        resp = lambda_client.get_function(FunctionName=func_name)
        # update code
        with open(lambda_zip_path, "rb") as f:
            lambda_client.update_function_code(FunctionName=func_name, ZipFile=f.read())
        print("[Lambda] Updated code for", func_name)
    except lambda_client.exceptions.ResourceNotFoundException:
        with open(lambda_zip_path, "rb") as f:
            resp = lambda_client.create_function(
                FunctionName=func_name,
                Runtime="python3.11",
                Role=role_arn,
                Handler="order_processor.lambda_handler",
                Code={"ZipFile": f.read()},
                Timeout=30,
                Environment={
                    "Variables": {
                        "AWS_REGION": settings.AWS_REGION,
                        "DDB_TABLE": settings.BEVFLOW_DDB_TABLE,
                        "LOGS_BUCKET": logs_bucket,
                        "SES_SENDER": settings.SES_SENDER
                    }
                }
            )
        print("[Lambda] Created function", func_name)
    # ensure event source mapping from SQS to Lambda
    # get queue ARN
    attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
    queue_arn = attrs["Attributes"]["QueueArn"]
    # check existing mappings
    mappings = lambda_client.list_event_source_mappings(EventSourceArn=queue_arn, FunctionName=func_name)
    if not mappings["EventSourceMappings"]:
        lambda_client.create_event_source_mapping(EventSourceArn=queue_arn, FunctionName=func_name, BatchSize=1, Enabled=True)
        print("[Lambda] Event source mapping created for SQS -> Lambda")

    return func_name

def get_role_arn_for_lambda():
    # This code assumes an IAM role named 'BevFlowLambdaRole-<env>' exists and has proper perms.
    # Best practice: create this role manually once with policy below, then bootstrap will use it.
    role_name = f"BevFlowLambdaRole-{settings.AWS_ENV_ID}"
    try:
        resp = iam.get_role(RoleName=role_name)
        return resp["Role"]["Arn"]
    except ClientError:
        print(f"[Bootstrap] IAM role {role_name} not found. Create this role and attach the policy listed in docs.")
        raise

def bootstrap_aws():
    try:
        # 1) SQS
        queue_url = ensure_sqs()
        ssm_put(settings.BEVFLOW_SQS_SSM_PARAM, queue_url)
        print("[Bootstrap] SQS ensured:", queue_url)

        # 2) SNS
        topic_arn = ensure_sns()
        ssm_put(settings.BEVFLOW_SNS_SSM_PARAM, topic_arn)
        print("[Bootstrap] SNS ensured:", topic_arn)

        # 3) subscribe SQS -> SNS and set queue policy
        subscribe_sqs_to_sns(topic_arn, queue_url)

        # 4) DynamoDB table
        ddb_table = ensure_dynamodb_table()
        print("[Bootstrap] DynamoDB table ensured:", ddb_table)

        # 5) logs S3 bucket
        logs_bucket = ensure_logs_bucket()
        print("[Bootstrap] Logs bucket ensured:", logs_bucket)

        # 6) package lambda
        zip_path = package_lambda()

        # 7) get role arn (must be pre-created)
        role_arn = get_role_arn_for_lambda()

        # 8) ensure lambda
        func_name = ensure_lambda(zip_path, role_arn, topic_arn, queue_url, logs_bucket)
        ssm_put(settings.BEVFLOW_LAMBDA_SSM_PARAM, func_name)

        print("[Bootstrap] AWS bootstrap complete.")
    except Exception as e:
        print("[Bootstrap] Error during bootstrap:", e)
