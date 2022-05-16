## Rekognition Streaming Video Events (Connected Home) Example

The connected home and managed security markets are dynamic and evolving, driven by an increased need for security, convenience, and entertainment. Amazon Rekognition Streaming Video Events detects objects (people, pets, and packages) in live video streams and returns the detected label(s), bounding box coordinates, zoomed-in images of the object(s) detected, and timestamps. The following will walk you through the steps needed to setup and configure Rekogntion Streaming Video Events to detect people, pets and packages in live video streams.


[Reference Architecture Diagram]

### Understanding Amazon Rekognition Streaming Video Events

Amazon Rekognition Streaming Video Events uses Amazon Kinesis Video Streams (KVS) to receive and process a video stream. You create a Rekognition video stream processor with parameters that show what you want the stream processor to detect from the video stream. In a typical connected home security use case, camera motion detection sensors trigger the stream processor to perform the analysis. When an object of interest is detected, Rekognition sends the detection results from streaming video events as notification on Amazon SNS and to storageAmazon S3 notifications. The following will walk you through the steps to setup and configure 

### Kinesis Video Stream Setup 

The Kinesis Video Streams (KVS) Producer SDKs enable you to build video pipelines leveraging the Kinesis Video Streams service.  The KVS service is a fully-managed video ingestion, storage, and playback service that automatically scales as the number of your devices scale.  This guide will help you get started with the KVS Producer SDK by demonstrating how to build (compile) and run a sample application that will stream a file to the KVS service.  

*Note: This guide purposely uses an EC2 to allow you to get started without requiring specific hardware and build environments.  Building the SDKs for specific hardware is an exercise left to the reader and outside the scope of this documentation.*

## Checkout and compile the KVS C++ Producer SDK

*Create an EC2 Instance with the following parameters:*

- Ubuntu 22.04 LTS 64-bit (x86)
- t2.micro
- 8 GB

You can select a larger instance type and more memory, but you must select Ubuntu 22.04 LTS for the following instructions to be relevant.

*Install the required dependencies*
Here we have provided a BASH script *kvs_setup.sh* that will help you get started, we recomend cloning this repository and updating the scripts to suit your enviornment. 

```bash 
./kvs_setup.sh
```

## Obtain IAM credentials for the sample application

After building the SDK, the binary *kvs_gstreamer_file_uploader_sample* should be in the build directory.  This application requires IAM credentials in order to access the KVS APIs.  The permissions for the credentials should allow the following actions:
 
- **"kinesisvideo:PutMedia"** 
- **"kinesisvideo:UpdateStream"** 
- **"kinesisvideo:GetDataEndpoint"** 
- **"kinesisvideo:UpdateDataRetention"** 
- **"kinesisvideo:DescribeStream"** 
- **"kinesisvideo:CreateStream"** 

#### Run the sample application

The *kvs_gstreamer_file_uploader_sample* requires 3 arguments; a stream name, the filename to be streamed to KVS, and a timestamp.  The command date +%s will return the unix epoch time in seconds and is included here for convenience. This will create a KVS stream which you can use to start your processing.

```bash
./kvs_gstreamer_file_uploader_sample DemoStream ~/package.mp4 `date +%s`
```

### Setting up Rekognition Streaming Video Events 

To setup Rekognition Streaming Video Events, you need a a Rekogntion VideoStreamProcessor to process the video stream from KVS, a S3 bucket to write processor results to and an SNS topic to send notifications to downstream applications. The following will provide you examples of creating these objects using the AWS CLI. 

1. Create a KVS stream, *note the stream’s resource name (ARN)* you will need this to create your stream processor.  

```bash
aws kinesisvideo create-stream --stream-name "DemoStream" \
 --data-retention-in-hours "24"
```
2. Create a S3 bucket for processor results. You’ll use the bucket to present artifacts (images, clips, bounding boxes etc) to down stream applications. 

```bash
aws s3api create-bucket \
 --bucket DemoStreamBucket \
 --region us-east-1
```
3. Create a SNS topic to send processor notifications to, make note of the resource name(ARN). You’ll use the SNS topic to trigger subsequent application processing. 

```bash
aws sns create-topic --name DemoStreamSNS
```

4. Create your stream processor, Here we've provided a simple python script *cr_stream_processor.py*, simply replace your resource name. You note the settings for ConnectedHome, the Labels to look for, and the MinConfidence. MinConfidence is the main tuning dial, the higher the confidence 

```python
import boto3

client = boto3.client('rekognition')

response = client.create_stream_processor(
    Input={
        'KinesisVideoStream': {
            'Arn': "your Stream's ARN "
        }
    },
    Output={
        'S3Destination': {
            'Bucket': 'tangelo-bucket',
            'KeyPrefix': 'tang'
        }
    },
    Name='name-of-stream-processor',
        Settings = {'ConnectedHome': {
            'Labels': ["PERSON", "PET", "PACKAGE","ALL"],
            'MinConfidence': 90
        }
        },

    RoleArn='Your ARN',
    NotificationChannel={
        'SNSTopicArn': "your SNS Queue ARN "
    }
)
print(response)
```

5. Start your stream processor, we've provided a sample pythong script *start_stream_processor.py* and here is an example of how to start your stream processor simply update the configuration to match your own. 

```python
import boto3

client = boto3.client('rekognition')

response = client.start_stream_processor(
    Name='tangelo1',
    StartSelector={
        'KVSStreamStartSelector': {
            'ProducerTimestamp': 1652717563529,
            'FragmentNumber': '1'
        }
    },
    StopSelector={
        'MaxDurationInSeconds': 120
    }
)
```



## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

