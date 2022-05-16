import boto3

client = boto3.client('rekognition')

response = client.start_stream_processor(
    Name='tangelo1',
    StartSelector={
        'KVSStreamStartSelector': {
            # 'ProducerTimestamp': 1652717563529,
            'FragmentNumber': '1'
        }
    },
    StopSelector={
        'MaxDurationInSeconds': 120
    }
)

print(response)
