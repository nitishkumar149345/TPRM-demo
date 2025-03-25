import boto3
import logging
from constants import keys
from fastapi import HTTPException, status
#Defining S3 client


def _get_client():
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=keys.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=keys.AWS_SECRET_ACCESS_KEY
        )

        return s3_client
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail= str(e))




class FileNotFoundError(Exception):
    pass

def download_file_content(bucket_name, object_name, output_file_path):

    try:
        s3_client = _get_client()
        s3_client.download_file(bucket_name, object_name, output_file_path)
        logging.info(f'{object_name} downloaded from s3')
        # contents = data['Body'].read()
        # return contents.decode("utf-8")
        return output_file_path

    except Exception as e:
        logging.info(f'Exception while downloading content: {str(e)}')
        raise FileNotFoundError

def upload_file_content(bucket_name, object_name, file_content):

    try:
        s3_client = _get_client()
        response = s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=file_content)
        logging.info(f'Response of put_object: {response}')
        return response

    except Exception as e:
        logging.info(f'Exception while put_object: {str(e)}')
        return None

def copy_file(source_bucket_name, source_key, destination_bucket_name, destination_key):

    try:

        copy_source = {
            'Bucket': source_bucket_name,
            'Key': source_key
        }

        s3_client = _get_client()
        response = s3_client.copy_object(CopySource=copy_source, Bucket=destination_bucket_name, Key=destination_key)
        logging.info(f'Response of copy_object: {response}')
        return response

    except Exception as e:
        logging.info(f'Exception while copy_object: {str(e)}')
        return None


def delete_file(bucket_name, source_key):

    try:
        s3_client = _get_client()
        response = s3_client.delete_object(Bucket=bucket_name, Key=source_key)
        logging.info(f'Response of delete_object: {response}')
        return response

    except Exception as e:
        logging.info(f'Exception while delete_object: {str(e)}')
        return None


def move_file(source_bucket_name, source_key, destination_bucket_name, destination_key):
    
    copy_file_response = copy_file(source_bucket_name, source_key, destination_bucket_name, destination_key)
    if not copy_file_response:
        return None

    return delete_file(source_bucket_name, source_key)