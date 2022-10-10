## python stream_simulator.py sns_topic_arn s3_bucket_name rekognition_role_arn path_to_uploader

import boto3
import os
from datetime import datetime
import uuid
import sys

rekognition_client = boto3.client('rekognition')
kvs_client = boto3.client('kinesisvideo')

video_list = os.listdir()
cwd = os.getcwd()

min_confidence_threshold = 75
supported_file_types = ['mp4']


args = sys.argv

sns_topic_arn = args[1]
s3_bucket_name = args[2]
rekognition_role_arn = args[3]
path_to_uploader = args[4]
def create_processor(kvs_stream_name, stream_processor_name):
    kvs_stream_arn = get_kvs_stream_arn(kvs_stream_name)
    response = rekognition_client.create_stream_processor(
        Input={
            'KinesisVideoStream': {
                'Arn': kvs_stream_arn
            }
        },
        Output={
            'S3Destination': {
                'Bucket': s3_bucket_name
            }
        },
        Name= stream_processor_name,
            Settings = {'ConnectedHome': {
                'Labels': ["PERSON", "PET", "PACKAGE","ALL"],
                'MinConfidence': min_confidence_threshold
            }
            },
        RoleArn=rekognition_role_arn,
        NotificationChannel={
            'SNSTopicArn': sns_topic_arn
        }
    )
    return response['StreamProcessorArn']

def kvs_upload_streamer(path_to_uploader, video_segment, kvs_stream_name):
    cmd = "{} {} {} $(date +%s)".format(path_to_uploader, kvs_stream_name, video_segment)
    os.system(cmd)
    
def process_stream(stream_processor_name, kvs_stream_name, start_time):
    stream_processor_arn = create_processor(kvs_stream_name, stream_processor_name)
    response = rekognition_client.start_stream_processor(
        Name=stream_processor_name,
        StartSelector={
            'KVSStreamStartSelector': {
                'ProducerTimestamp': start_time
            }
        },
        StopSelector={
            'MaxDurationInSeconds': 120
        }
    )

def get_kvs_stream_arn(stream_name):
    response = kvs_client.describe_stream(
        StreamName=stream_name,
    )
    return response['StreamInfo']['StreamARN']

def main():
    for video_segment in video_list:
        if video_segment.split('.')[-1] not in supported_file_types:
            continue
        start_time = round(datetime.now().timestamp())
        execution_id = str(uuid.uuid4())[:8]
        
        kvs_stream_name="sveStream{}".format(execution_id)
        
        kvs_upload_streamer(path_to_uploader, video_segment, kvs_stream_name)
    
        process_stream("sveProcessor{}".format(execution_id), kvs_stream_name, start_time)
    
if __name__ == '__main__':
    main()