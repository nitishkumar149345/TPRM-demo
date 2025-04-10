from dotenv import load_dotenv
from logger_config.logs import logger
import os

load_dotenv()


class KeyNotFoundError(Exception):
    def __init__(self, key_name):
        self.key_name = key_name

    def __str__(self):
        return f"Environment variable '{self.key_name}' not found. Please set it in your environment."


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', None)

AWS_ACCESS_KEY_ID= os.getenv('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY= os.getenv('AWS_SECRET_ACCESS_KEY', None)
AWS_BUCKET_NAME= os.getenv('AWS_BUCKET_NAME', None)
BASE_APPLICATION_URL= os.getenv('BASE_URL',None)
MILVUS_HOST_URI= os.getenv("MILVUS_HOST_URI", None)
# MILVUS_PORT= os.getenv("MILVUS_PORT", None)
GOOGLE_API_KEY= os.getenv("GOOGLE_API_KEY", None)


if not OPENAI_API_KEY:
    logger.critical('Pass OPENAI_API_KEY or Set it as env variable')

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    logger.critical('Provide aws s3 access key or secret key')


if not AWS_BUCKET_NAME:
    logger.critical('Provide aws s3 bucket name')

if not BASE_APPLICATION_URL:
    # raise KeyNotFoundError('base_application_url')
    logger.critical('Provide base url')



if not MILVUS_HOST_URI or not MILVUS_HOST_URI.startswith('http'):
    # raise KeyNotFoundError('milvus uri')
    logger.critical('Milvus uri not provided or format wrong')