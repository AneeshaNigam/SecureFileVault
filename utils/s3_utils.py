import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from config import Config
import time

s3 = boto3.client(
    's3',
    aws_access_key_id=Config.AWS_ACCESS_KEY,
    aws_secret_access_key=Config.AWS_SECRET_KEY,
    region_name=Config.AWS_REGION
)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def upload_to_s3(file, bucket_name=None):
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
    
    if bucket_name is None:
        bucket_name = Config.S3_BUCKET
    
    try:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_filename = f"{timestamp}-{filename}"
        
        # Advanced Feature 6: Server-Side Encryption
        s3.upload_fileobj(
            file,
            bucket_name,
            unique_filename,
            ExtraArgs={
                "ACL": "private",
                "ContentType": file.content_type,
                "ServerSideEncryption": "AES256",
                "Metadata": {
                    "original-filename": filename,
                    "upload-timestamp": timestamp
                }
            }
        )
        
        return {
            "filename": filename,
            "s3_key": unique_filename,
            "timestamp": timestamp
        }
    except Exception as e:
        raise Exception(f"Upload failed: {str(e)}")

def generate_presigned_url(s3_key, expiration=3600):
    """Generate pre-signed URL with download tracking"""
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': Config.S3_BUCKET,
                'Key': s3_key,
                'ResponseContentDisposition': 'attachment'  # Force download
            },
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        raise Exception(f"URL generation failed: {str(e)}")

# Advanced Feature 7: Access Revocation
def revoke_access(s3_key):
    try:
        s3.put_object_acl(
            Bucket=Config.S3_BUCKET,
            Key=s3_key,
            ACL='private'
        )
        return True
    except Exception as e:
        raise Exception(f"Revocation failed: {str(e)}")

# Advanced Feature 8: File Metadata
def get_file_metadata(s3_key):
    try:
        response = s3.head_object(
            Bucket=Config.S3_BUCKET,
            Key=s3_key
        )
        return {
            'last_modified': response['LastModified'],
            'size_mb': round(response['ContentLength'] / (1024 * 1024), 2),
            'storage_class': response.get('StorageClass', 'STANDARD'),
            'encryption': response.get('ServerSideEncryption', 'None')
        }
    except Exception as e:
        raise Exception(f"Metadata fetch failed: {str(e)}")