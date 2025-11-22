# bevflow/aws/lambda/order_processor.py
import json
import os
import uuid
from datetime import datetime
import boto3

# Use your PyPI package from PyPI
try:
    from dublindistance import calculate_distance
except Exception as e:
    # graceful fallback
    def calculate_distance(a, b):
        return 0

REGION = os.environ.get("AWS_REGION", "us-east-1")
DDB_TABLE = os.environ.get("DDB_TABLE", "BevFlowOrders")
SES_SENDER = os.environ.get("SES_SENDER", "no-reply@bevflow.com")
# We will reuse your existing bucket via a small helper: this code expects the bucket name passed via env
LOGS_BUCKET = os.environ.get("LOGS_BUCKET")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
ses = boto3.client("ses", region_name=REGION)

def compute_eta(customer_area, manufacturer_area):
    try:
        dist_km = calculate_distance(manufacturer_area, customer_area)
    except Exception:
        dist_km = 0
    eta_days = 3 + int(dist_km / 5)
    return dist_km, eta_days

def store_order_summary(ddb_table_name, message):
    if not ddb_table_name:
        return
    table = dynamodb.Table(ddb_table_name)
    item = {
        "order_id": str(message.get("order_id")),
        "product_id": str(message.get("product_id")),
        "product_name": message.get("product_name"),
        "quantity": int(message.get("quantity", 0)),
        "customer_id": str(message.get("customer_id")),
        "customer_username": message.get("customer_username"),
        "customer_area_code": message.get("customer_area_code"),
        "manufacturer_id": str(message.get("manufacturer_id")),
        "manufacturer_username": message.get("manufacturer_username"),
        "manufacturer_email": message.get("manufacturer_email"),
        "manufacturer_area_code": message.get("manufacturer_area_code"),
        "created_at": message.get("created_at"),
        "status": "PROCESSED"
    }
    table.put_item(Item=item)

def save_log_to_s3(bucket, key, body):
    if not bucket:
        return
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(body).encode("utf-8"))
    except Exception as e:
        print("S3 log write error:", e)

def send_email(to_address, subject, text_body, html_body):
    if not SES_SENDER or not to_address:
        print("SES sender or recipient missing; skipping email.")
        return False
    try:
        ses.send_email(
            Source=SES_SENDER,
            Destination={"ToAddresses": [to_address]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Text": {"Data": text_body},
                    "Html": {"Data": html_body}
                }
            }
        )
        return True
    except Exception as e:
        print("SES send error:", e)
        return False

def handler_process_message(msg):
    # Compute distance & ETA
    cust_area = msg.get("customer_area_code", "")
    manu_area = msg.get("manufacturer_area_code", "")
    dist_km, eta_days = compute_eta(cust_area, manu_area)

    # Save to DynamoDB
    try:
        store_order_summary(DDB_TABLE, msg)
    except Exception as e:
        print("DDB store error:", e)

    # Save logs to S3 (reuse existing bucket passed by env)
    log_bucket = LOGS_BUCKET
    log_key = f"order-logs/{msg.get('order_id')}.json"
    save_log_to_s3(log_bucket, log_key, {"message": msg, "distance_km": dist_km, "eta_days": eta_days})

    # Send SES email to manufacturer
    to_email = msg.get("manufacturer_email")
    if to_email:
        subject = f"New Order #{msg.get('order_id')} — {msg.get('product_name')}"
        text = (
            f"Order {msg.get('order_id')} placed by {msg.get('customer_username')}.\n"
            f"Quantity: {msg.get('quantity')}\nDistance: {dist_km} km\nEstimated delivery: {eta_days} days\n"
        )
        html = f"""
            <p>Order <b>{msg.get('order_id')}</b> placed by <b>{msg.get('customer_username')}</b>.</p>
            <p>Product: <b>{msg.get('product_name')}</b></p>
            <p>Quantity: <b>{msg.get('quantity')}</b></p>
            <p>Distance: <b>{dist_km} km</b></p>
            <p>Estimated delivery: <b>{eta_days} days</b></p>
        """
        send_email(to_email, subject, text, html)

def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    for record in event.get("Records", []):
        try:
            body = json.loads(record.get("body", "{}"))
        except Exception as e:
            print("Invalid JSON in SQS body", e)
            continue

        try:
            handler_process_message(body)
        except Exception as e:
            print("Processing error:", e)

    return {"statusCode": 200}
