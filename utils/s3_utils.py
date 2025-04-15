import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def upload_to_s3(file, bucket_name=None):
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
    
    if bucket_name is None:
        bucket_name = Config.S3_BUCKET
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=Config.AWS_ACCESS_KEY,
        aws_secret_access_key=Config.AWS_SECRET_KEY,
        region_name=Config.AWS_REGION
    )
    
    try:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_filename = f"{timestamp}-{filename}"
        
        s3.upload_fileobj(
            file,
            bucket_name,
            unique_filename,
            ExtraArgs={
                "ACL": "private",
                "ContentType": file.content_type
            }
        )
        
        file_url = f"https://{bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{unique_filename}"
        
        return {
            "filename": filename,
            "s3_key": unique_filename,
            "file_url": file_url,
            "timestamp": timestamp
        }
    except NoCredentialsError:
        raise Exception("AWS credentials not available")
    except ClientError as e:
        raise Exception(f"AWS Client Error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error uploading file: {str(e)}")