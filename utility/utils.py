import boto3
import logging

from constants.keys import (
    AWS_S3_ACCESS_KEY,
    AWS_S3_SECRET_KEY, 
    AWS_S3_BUCKET_NAME,
)

#Defining S3 client

s3_client = boto3.client('s3')


def download_file_content(bucket_name, object_name, output_file_path):

    try:

        data = s3_client.get_object(bucket_name, object_name, output_file_path)
        # logging.info(f'File content: {data}')
        # contents = data['Body'].read()
        # return contents.decode("utf-8")
        return output_file_path

    except Exception as e:
        logging.info(f'Exception while downloading content: {str(e)}')
        return None

def upload_file_content(bucket_name, object_name, file_content):

    try:

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
        response = s3_client.copy_object(CopySource=copy_source, Bucket=destination_bucket_name, Key=destination_key)
        logging.info(f'Response of copy_object: {response}')
        return response

    except Exception as e:
        logging.info(f'Exception while copy_object: {str(e)}')
        return None


def delete_file(bucket_name, source_key):

    try:

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