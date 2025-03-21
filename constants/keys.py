from dotenv import load_dotenv
from logger_config.logs import logger
import os

load_dotenv()


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', None)

AWS_S3_ACCESS_KEY= os.getenv('AWS_S3_ACCESS_KEY', None)
AWS_S3_SECRET_KEY= os.getenv('AWS_S3_SECRET_KEY', None)
AWS_S3_BUCKET_NAME= os.getenv('AWS_S3_BUCKET_NAME', None)


if not OPENAI_API_KEY:
    logger.info('Pass OPENAI_API_KEY or Set it as env variable')

if not AWS_S3_ACCESS_KEY or not AWS_S3_SECRET_KEY:
    logger.info('Provide aws s3 access key or secret key')


if not AWS_S3_BUCKET_NAME:
    logger.info('Provide aws s3 bucket name')