import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS Configuration
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET = os.getenv('S3_BUCKET')
    
    # App Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'pdf,doc,docx,txt,png,jpg,jpeg,gif').split(','))
    MAX_CONTENT_LENGTH = eval(os.getenv('MAX_CONTENT_LENGTH', '16 * 1024 * 1024'))  # 16MB