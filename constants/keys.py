from dotenv import load_dotenv
from logger_config.logs import logger
import os

load_dotenv()


class KeyNotFoundError(Exception):

    def __str__(self,):
        return 'URL not found, set it as env variable'

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', None)

AWS_ACCESS_KEY_ID= os.getenv('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY= os.getenv('AWS_SECRET_ACCESS_KEY', None)
AWS_BUCKET_NAME= os.getenv('AWS_BUCKET_NAME', None)
BASE_APPLICATION_URL= os.getenv('BASE_URL',None)
MILVUS_HOST_URI= os.getenv("MILVUS_HOST_uri", None)
# MILVUS_PORT= os.getenv("MILVUS_PORT", None)



if not OPENAI_API_KEY:
    logger.info('Pass OPENAI_API_KEY or Set it as env variable')

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    logger.info('Provide aws s3 access key or secret key')


if not AWS_BUCKET_NAME:
    logger.info('Provide aws s3 bucket name')

if not BASE_APPLICATION_URL:
    # raise KeyNotFoundError
    logger.info('Provide base url')

if not MILVUS_HOST_URI:
    # raise KeyNotFoundError
    logger.info('Provide Milvus VDB url')