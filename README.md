## Rekognition Streaming Video Events (Connected Home) Example

The connected home and managed security markets are dynamic and evolving, driven by an increased need for security, convenience, and entertainment. Amazon Rekognition Streaming Video Events detects objects (people, pets, and packages) in live video streams and returns the detected label(s), bounding box coordinates, zoomed-in images of the object(s) detected, and timestamps. The following will walk you through the steps needed to setup and configure Rekogntion Streaming Video Events to detect people, pets and packages in live video streams.


![Reference Architecture Diagram](https://github.com/aws-samples/rekognition-streaming-video-events/blob/main/img/sve_architecture.jpg?raw=true)

### Understanding Amazon Rekognition Streaming Video Events

Amazon Rekognition Streaming Video Events uses Amazon Kinesis Video Streams (KVS) to receive and process a video stream. You create a Rekognition video stream processor with parameters that show what you want the stream processor to detect from the video stream. In a typical connected home security use case, a in-camera motion detection sensor triggers the Rekognition stream processor to perform the analysis (detection of people, packages, and pets). When an object of interest is detected, Rekognition sends the results as a notification to Amazon SNS and to Amazon S3. The following will walk you through the steps to setup and configure Rekognition streaming video events for the *connected home* use case.

### Kinesis Video Stream Setup 

The Kinesis Video Streams (KVS) Producer SDKs enable you to build video pipelines leveraging the Kinesis Video Streams service.  The KVS service is a fully-managed video ingestion, storage, and playback service that automatically scales as the number of your devices scale.  This guide will help you get started with the KVS Producer SDK by demonstrating how to build (compile) and run a sample application that will stream a file to the KVS service.  

*Note: This guide purposely uses an EC2 to allow you to get started without requiring specific hardware and build environments.  Building the SDKs for specific hardware is an exercise left to the reader and outside the scope of this documentation.*

## Checkout and compile the KVS C++ Producer SDK

*Create an EC2 Instance with the following parameters:*

- Ubuntu 22.04 LTS 64-bit (x86)
- t2.micro
- 8 GB

You can select a larger instance type and more memory, but you must select Ubuntu 22.04 LTS for the following instructions to be relevant.

## Create a User and provide appropriate permissions

Using the AWS console navigate to Identity and Access Management(IAM). Here you are going to create a new user which you will use to log into your EC2 instance you created above. When you create the user select AWS credential type: select Access key, this is used for programmatic access to AWS. This will also create an access key ID and secret access key for the AWS API, CLI, SDK and other development tools. Make note of the access key ID and the secret access key you’ll need these to configure the AWS client on your EC2 instance. 

[Setting up your Amazon Rekognition Video and Amazon Kinesis resources](https://docs.aws.amazon.com/rekognition/latest/dg/streaming-labels-setting-up.html#streaming-labels-giving-access)

### Configure AWS Command Line Interface (CLI)

On your ubuntu instance you'll need to configure the AWS Command Line Interface (CLI). To do this you'll need your AWS_ACCESS_KEY_ID and  AWS_SECRET_ACCESS_KEY and a defaut region.

```bash
# follow the instructions 
aws configure 
```

### Install the required dependencies and build the SDK

Once you've AWS Command Line Interface (CLI) is configured, you are now ready to install the dependancies and build the SDK. Here we have provided a BASH script *kvs_setup.sh* that will help you get started, we recomend cloning this repository and updating the  *kvs_setup.sh* script to suit your enviornment. 

```bash 
./kvs_setup.sh
```

## Obtain IAM credentials for the sample application

After building the SDK, the binary *kvs_gstreamer_file_uploader_sample* should be in the **build directory**.  This application requires IAM credentials in order to access the KVS APIs.  The permissions for the credentials should allow the following actions:
 
- **"kinesisvideo:PutMedia"** 
- **"kinesisvideo:UpdateStream"** 
- **"kinesisvideo:GetDataEndpoint"** 
- **"kinesisvideo:UpdateDataRetention"** 
- **"kinesisvideo:DescribeStream"** 
- **"kinesisvideo:CreateStream"** 

After obtaining the permissions, export your enviornment variables them prior to executing the *kvs_gstreamer_file_uploader_sample.* 
 
```bash
export AWS_ACCESS_KEY_ID=<your access key id>
export AWS_SECRET_ACCESS_KEY=<your secret access key>
export AWS_DEFAULT_REGION=<your region>
```

## Setting up Rekognition Streaming Video Events 

To setup Rekognition Streaming Video Events, you need a Rekogntion VideoStreamProcessor to process the video stream from KVS, a S3 bucket to write processor results to and an SNS topic to send notifications to downstream applications. The following will provide you examples of creating these objects. 

#### 1. Run the sample application to create a KVS stream

The *kvs_gstreamer_file_uploader_sample* requires 3 arguments; a stream name, the filename to be streamed to KVS, and a timestamp.  The command `date +%s` will return the unix epoch time in seconds and is included here for convenience. This will create a KVS stream named **DemoStream** which you can use to start your processing.

```bash
./kvs_gstreamer_file_uploader_sample DemoStream /sample-video/package.mp4 `date +%s`
```

Navigate to KVS on the AWS console and note KVS stream’s resource name (ARN), you will need this to create your stream processor.  


##### Alternate: Create a KVS stream using the AWS CLI  

```bash
aws kinesisvideo create-stream --stream-name "DemoStream" \
 --data-retention-in-hours "24"
```
*note the stream’s resource name (ARN)* you will need this to create your stream processor.  

####  2. Create a S3 bucket for processor results. 

You’ll use the bucket to present artifacts (images, clips, bounding boxes etc) to down stream applications. 

```bash
aws s3api create-bucket \
 --bucket demo-stream-bucket \
 --region us-east-1
```
#### 3. Create a SNS topic to send processor notifications

You'll use the SNS topic to send notifications to downstream applicaitons. Besure to make note of the resource name(ARN). You’ll use the SNS topic to trigger subsequent application processing. 

```bash
aws sns create-topic --name demo-stream-sns
```

#### 4. Create a Rekogntion Stream Processor 

Here we've provided a simple python script *cr_stream_processor.py*, simply replace your KVS stream's resource name(ARN), S3 bucket name, ans SNS resource name(ARN). Note the settings for ConnectedHome: the *Labels* to look for and *MinConfidence*. *MinConfidence* is our main tuning dial, the higher the confidence the more precise your stream processor will be in detecting these labels. 

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
            'Bucket': 'your-bucket-name'
        }
    },
    Name='demo-stream-processor',
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

#### 5. Trigger  your stream processor, 

Here we've provided a sample python script *start_stream_processor.py* and here is an example of how to start your stream processor simply update the configuration to match your own. When triggering the script you can specify the durration of the video to search for labels. 

```python
import boto3

client = boto3.client('rekognition')

response = client.start_stream_processor(
    Name='demo-stream-processor',
    StartSelector={
        'KVSStreamStartSelector': {
            'ProducerTimestamp': 'epoch-time-stamp'
        }
    },
    StopSelector={
        'MaxDurationInSeconds': 120
    }
)
```

## Analyzing Rekognition Streaming Video Events 

To analyze the Rekognition Streaming Video Events, you need to capture the stream processor results that are sent to the SNS topic and store in an AWS Glue Table. To do so, you can deploy the AWS CloudFormation template. The template creates the following infrastructure:

- Amazon SNS Topic to capture the Rekognition Streaming Video Events
- Amazon Kinesis Data Firehose to consume the events from the SNS topic
- Amazon S3 Bucket to store the underlying data
- AWS Lambda Function to processs the Firehose stream, write the processed data to S3, and update the table
- AWS Glue Database that will store the processing results table.

1. Deploy the [CloudFormation template](./cloudformation/sve-template.yaml) in your account.

2. Once the stack creates successfully, download your videos to your EC2 instance execute an `aws s3 sync`

3. Then, execute the stream simulator Python script to stream the downloaded videos to Kinesis Video Streams. The script will automatically start Rekogntion Stream Processors to process the streaming video.

```bash
python stream_simulator.py sns_topic_arn s3_bucket_name rekognition_role_arn path_to_uploader
```

4. Analyze the results using the SVE Profile Report.

```bash
python sve_profile_report.py
```
This will produce a sve_profile_report.html file which you can use to analyse the results of your videos. 

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

