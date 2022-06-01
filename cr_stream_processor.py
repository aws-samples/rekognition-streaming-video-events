import boto3

# add your ARNs here :
KinesisVideoStreamARN = ""
SNSTopicARN = ""

# add your bucket and stream processor names here:
S3BucketName = ""
StreamProcessorName = ""

client = boto3.client('rekognition')

response = client.create_stream_processor(
    Input={
        'KinesisVideoStream': {
            'Arn': KinesisVideoStreamARN
        }
    },
    Output={
        'S3Destination': {
            'Bucket': S3BucketName
        }
    },
    Name= StreamProcessorName,
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
