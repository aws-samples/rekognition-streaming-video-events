#!/usr/bin/bash
echo starting KVS setup

# Install the required dependencies
echo Installing required dependencies
sudo apt-get update
sudo apt-get install pkg-config cmake m4 git g++
sudo apt-get install libssl-dev libcurl4-openssl-dev liblog4cplus-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-bad gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools

# Clone the KVS C++ Producer SDK version 3.3.0
echo Cloning the KVS C++ Producer SDK version 3.3.0
git clone --branch v3.3.0 https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git

# Create the build directory
echo Creating build directory 
mkdir -p amazon-kinesis-video-streams-producer-sdk-cpp/build
cd amazon-kinesis-video-streams-producer-sdk-cpp/build

# Build the SDK and sample applications
echo Building the SDK and sample applications 
cmake .. -DBUILD_GSTREAMER_PLUGIN=ON -DBUILD_DEPENDENCIES=OFF
make

# Export the GST_PLUGIN_PATH
echo Export the GST_PLUGIN_PATH
export GST_PLUGIN_PATH=`pwd`:$GST_PLUGIN_PATH

# Finally configure your AWS enviornment for next steps 
echo aws configure
aws configure



