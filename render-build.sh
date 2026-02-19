#!/usr/bin/env bash
set -o errexit

# 1. System packages install karein (tput ke liye ncurses)
apt-get update
apt-get install -y ncurses-bin

# 2. Python dependencies install karein
pip install --upgrade pip
pip install -r requirements.txt

# 3. FFmpeg install karein (YouTube downloads ke liye zaroori hai)
mkdir -p /tmp/ffmpeg
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ --strip-components=1 -C /tmp/ffmpeg

# 4. Path set karein
export PATH=$PATH:/tmp/ffmpeg
