import http.client
import boto3
import os
import socket
from botocore.exceptions import ClientError

AWS_REGION = os.environ['REGION']
SENDER_EMAIL=os.environ['SENDER_EMAIL']
RECIPIENT_EMAIL = os.environ['RECIPIENT_EMAIL']
SUBJECT = os.environ['SUBJECT']

# Initialize the AWS SDK client
ses_client = boto3.client('ses', region_name=AWS_REGION)

def lambda_handler(event, context):
    servers = [
        {
            'name': 'Prometheus',
            'ip': os.environ.get('PROMETHEUS_IP'),
            'port': int(os.environ.get('PROMETHEUS_PORT')),
            'url': os.environ.get('PROMETHEUS_URL'),
            'expected_status': 200
        }
        # We can add more servers here as needed.
    ]
    
    for server in servers:
        check_server_health(server)

def check_server_health(server):
    ip = server['ip']
    port = server['port']
    url = server['url']
    expected_status = server['expected_status']
    name = server['name']
    
    if not ip or not port or not url:
        print(f"{name} IP, port, or URL is not provided in environment variables.")
        return
    
    try:
        conn = http.client.HTTPConnection(ip, port, timeout=10)
        conn.request("GET", url)
        response = conn.getresponse()
        status_code = response.status
        
        if status_code != expected_status:
            send_email_notification(f"{name} server cannot be reached. Please investigate.")
            print(f"{name} health check failed. Status code: {status_code}")
        else:
            print(f"{name} health check passed.")
        
    except socket.timeout:
        send_email_notification(f"{name} server is unreachable. Please investigate.")
        print(f"Error: {name} server is unreachable.")
    
    except Exception as e:
        send_email_notification(f"{name} server cannot be reached. Please investigate.")
        print(f"Error occurred while checking {name} health. Error: {str(e)}")

def send_email_notification(message):
    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': [RECIPIENT_EMAIL]
            },
            Message={
                'Subject': {'Data': SUBJECT},
                'Body': {'Text': {'Data': message}}
            }
        )
        print("Email sent successfully: ", response)
    except ClientError as e:
        print("Error sending email: ", e)
