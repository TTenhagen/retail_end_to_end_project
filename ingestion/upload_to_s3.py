import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name = os.getenv("AWS_REGION", "us-east-1")
)

BUCKET = os.getenv("S3_BUCKET", "retail-raw")

files = (
    "stores/stores.csv":         "data/stores.csv",
    "fact/fact.csv":             "data/fact.csv",
    "department/department.csv": "data/department.csv"
)

for s3_key, local_path in files.items():
    full_path = os.path.abspath(local_path)
    s3.upload_file(Filename=full_path, Bucket=BUCKET, Key=s3_key)
    print(f"Uploaded {local_path} -> s3://{BUCKET}/{s3_key}")

print("All files uploaded successfully")
