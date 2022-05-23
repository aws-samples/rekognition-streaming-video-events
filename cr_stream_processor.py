import boto3

# add your ARNs here 
KinesisVideoStreamARN = ""
SNSTopicARN = ""

client = boto3.client('rekognition')

response = client.create_stream_processor(
    Input={
        'KinesisVideoStream': {
            'Arn': KinesisVideoStreamARN
        }
    },
    Output={
        'S3Destination': {
            'Bucket': 'tangelo-bucket',
            'KeyPrefix': 'tang'
        }
    },
    Name='tangelo1',
        Settings = {'ConnectedHome': {
            'Labels': ["PERSON", "PET", "PACKAGE","ALL"],
            'MinConfidence': 90
        }
        },

    RoleArn='YourRoleARN',
    NotificationChannel={
        'SNSTopicArn': SNSTopicARN
    }
)
print(response)
