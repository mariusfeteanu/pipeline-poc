import os

from dotenv import load_dotenv, find_dotenv
import boto3
from io import BytesIO

load_dotenv(find_dotenv()) 


s3 = boto3.resource(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
    aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD")
)

for bucket in s3.buckets.all():
    print("Bucket:", bucket.name)