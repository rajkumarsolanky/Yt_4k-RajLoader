#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

mkdir -p /tmp/ffmpeg
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ --strip-components=1 -C /tmp/ffmpeg

export PATH=$PATH:/tmp/ffmpeg
