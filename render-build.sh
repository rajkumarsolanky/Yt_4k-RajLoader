#!/usr/bin/env bash
set -o errexit

# 1. Python dependencies install karein
pip install -r requirements.txt

# 2. FFmpeg install karne ke liye (Download URL ke saath)
mkdir -p /tmp/ffmpeg
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ --strip-components=1 -C /tmp/ffmpeg

# 3. Path set karein taaki system ise dhoond sake
export PATH=$PATH:/tmp/ffmpeg
