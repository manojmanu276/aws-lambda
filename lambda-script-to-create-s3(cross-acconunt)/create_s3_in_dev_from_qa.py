#here i am trying to create a s3 bucket in aws-dev-account using a lambda function in my aws-qa-account and lambda function should pick bucket name from a response body.
#The bucket name should be in the format bucket_name-customer_id-random_number
#aws_management_console--->lamda---->create_function--->give_appropriate_name---->click_on_the_function_created--->code---->copy the below code

import boto3
import os
import json
import logging
import random
import string

logger=logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
  # Generate a random number to append to the bucket name

  random_number = ''.join(random.choices(string.digits, k=4))

  # extracting customer_id and bucket_name from the response(event) body
  logger.info("received event : {}".format(event))
  if 'body' in event:
    event_body = json.loads(event['body'])
    customer_id = event_body.get('customer_id')
    bucket_name = event_body.get('bucket_name')

  else:
    customer_id = event.get('customer_id')
    bucket_name = event.get('bucket_name')

  #define aws-dev-account-details
  dev_account_id = os.environ['DEV_ACCOUNT_ID']     #the variables can be declared on aws lamda console----->your_lamda_function--->configurations--->environment-variables tab
  role_name = os.environ['CA_ROLE_NAME']            #refer the value to these variables in os.py file. This is the role name you have to create in qa-account and attach the trust policy with dev-account

  # assume the cross-account-role in the dev-account
  sts_client = boto3.client('sts')
  response = sts_client.assume_role(
    RoleArn=os.environ['ROLE_ARN'],                 # This is the role you have to create in dev-account, with permissions to create s3-bucket and trust policy with qa-account.
    RoleSessionName='CrossAccountSession'
  )

  #Extract temporary credentials
  temp_credentials = response['credentials']

  #create s3 client using temporary credentials
  s3_client = boto3.client(
    's3',
    aws_access_key_id=temp_credentials['AccessKeyId'],
    aws_secret_access_key=temp_credentials['SecretAccessKey'],
    aws_session_token=temp_credentials['SessionToken'],
  )

  # specify the region for bucket creation
  region = os.environ['REGION']
  bucket_name_with_customer_id = f'{bucket_name}-{customer_id}-{random_number}'

  #create s3 bucket in dev account
  s3_client.create_bucket(
    Bucket=bucket_name_with_customer_id,
    CreateBucketConfiguration={'LocationConstraint': region}
  )
  return {
    'statusCode' : 200,
    'body' : f'S3 bucket {bucket_name} created successfully in dev account.'
  }
  
