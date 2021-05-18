import socket

import boto3
from botocore.exceptions import ClientError

from cuwb_sensor.tools.logging import logger

EMAIL_SENDER = f"{socket.gethostname()}@wildflowerschools.org"


def send_email(to, subject, message):
    client = boto3.client(
        'ses',
        region_name='us-east-1'
    )

    try:
        client.send_email(
            Destination={
                'ToAddresses': [to],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': "UTF-8",
                        'Data': message,
                    },
                },
                'Subject': {
                    'Charset': "UTF-8",
                    'Data': subject,
                },
            },
            Source=EMAIL_SENDER,
        )

    except ClientError as e:
        logger.error("Failed sending email: {}".format(e.response['Error']['Message']))