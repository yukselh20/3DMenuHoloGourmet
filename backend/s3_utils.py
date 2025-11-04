import os
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pathlib import Path
from typing import BinaryIO

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# S3 Configuration from environment variables
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
S3_REGION = os.environ.get('S3_REGION', 'us-east-1')

s3_client = None
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and S3_BUCKET_NAME:
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=S3_REGION
        )
        # Check if bucket exists and is accessible
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        logging.info(f"Successfully connected to S3 bucket: {S3_BUCKET_NAME}")
    except ClientError as e:
        logging.error(f"Failed to connect to S3. Error: {e}. Falling back to mock storage.")
        s3_client = None
    except Exception as e:
        logging.error(f"An unexpected error occurred during S3 initialization: {e}. Falling back to mock storage.")
        s3_client = None


def upload_file_obj_to_s3(file_obj: BinaryIO, key: str, content_type: str = 'application/zip') -> str:
    """
    Uploads a file-like object to S3 using streaming and returns the URL.
    If S3 is not configured, it returns a mock URL for local development.
    """
    if not s3_client or not S3_BUCKET_NAME:
        # Mock S3 upload for local development if client is not available
        logging.warning("S3 client not configured. Using mock upload URL.")
        # We still need to consume the file object to avoid issues
        file_obj.read()
        return f"https://{S3_BUCKET_NAME or 'mock-bucket'}.s3.{S3_REGION}.amazonaws.com/{key}"

    try:
        s3_client.upload_fileobj(
            file_obj,
            S3_BUCKET_NAME,
            key,
            ExtraArgs={'ContentType': content_type}
        )
        url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{key}"
        logging.info(f"Successfully uploaded {key} to S3 via streaming.")
        return url
    except ClientError as e:
        logging.error(f"Error uploading to S3: {e}")
        # Re-raise the exception to be handled by the API endpoint
        raise e


def upload_file_to_s3(file_content: bytes, key: str, content_type: str = 'application/zip') -> str:
    """
    DEPRECATED: Uploads a file from bytes to S3 and returns the URL.
    Prefer `upload_file_obj_to_s3` for streaming.
    """
    if not s3_client or not S3_BUCKET_NAME:
        logging.warning("S3 client not configured. Using mock upload URL.")
        return f"https://{S3_BUCKET_NAME or 'mock-bucket'}.s3.{S3_REGION}.amazonaws.com/{key}"

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=content_type
        )
        url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{key}"
        logging.info(f"Successfully uploaded {key} to S3.")
        return url
    except ClientError as e:
        logging.error(f"Error uploading to S3: {e}")
        raise e