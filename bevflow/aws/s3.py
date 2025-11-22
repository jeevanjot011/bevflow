import boto3
import random
import string
import json
from botocore.exceptions import ClientError
from django.conf import settings

ssm = boto3.client("ssm", region_name=settings.AWS_REGION)
s3 = boto3.client("s3", region_name=settings.AWS_REGION)


# -----------------------
# Check if bucket exists
# -----------------------
def bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError:
        return False


# -----------------------
# Generate random suffix
# -----------------------
def get_random_suffix():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


# -----------------------
# Main bucket resolver
# -----------------------
def get_or_create_bucket_name():
    """
    ALWAYS returns a working bucket name.
    Handles:
    - Missing SSM parameter
    - Deleted buckets
    - Wrong region buckets
    """
    param_name = settings.AWS_PARAM_BUCKET

    # 1. Try to fetch from SSM
    try:
        response = ssm.get_parameter(Name=param_name)
        bucket_name = response["Parameter"]["Value"]
        print(f"[S3] Found stored bucket in SSM: {bucket_name}")

        # 1A — Check if bucket still exists
        if bucket_exists(bucket_name):
            print(f"[S3] Bucket exists. Using: {bucket_name}")
            return bucket_name
        else:
            print(f"[S3] Bucket '{bucket_name}' does NOT exist anymore. Creating new one...")

    except ssm.exceptions.ParameterNotFound:
        print("[S3] No bucket stored in SSM. Creating new one...")

    # 2. Create brand new bucket name
    suffix = get_random_suffix()
    bucket_name = f"bevflow-{settings.AWS_ENV_ID}-{suffix}"

    # 3. Create bucket
    try:
        if settings.AWS_REGION == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION}
            )
        print(f"[S3] Created new bucket: {bucket_name}")

    except ClientError as e:
        print("[S3] Error creating bucket:", e)
        raise e

    # 4. Store new bucket in SSM (overwrite old)
    ssm.put_parameter(
        Name=param_name,
        Value=bucket_name,
        Type="String",
        Overwrite=True
    )
    print(f"[S3] Updated SSM parameter with bucket: {bucket_name}")

    return bucket_name


def upload_image(file_obj, filename):
    bucket_name = get_or_create_bucket_name()
    s3.upload_fileobj(file_obj, bucket_name, filename)

    # Generate a presigned URL valid for 7 days
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': filename},
        ExpiresIn=604800  # 7 days
    )
    return url
def generate_presigned_url(key, expiry=3600):
    """
    Generates a temporary (presigned) URL for S3 object.
    Keeps bucket PRIVATE but allows temporary public access.
    """
    bucket_name = get_or_create_bucket_name()

    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket_name,
                "Key": key
            },
            ExpiresIn=expiry
        )
        return url

    except ClientError as e:
        print("[S3] Error generating presigned URL:", e)
        return None
