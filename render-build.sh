#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

curl -L  | tar -xJ --strip-components=1 -C /tmp
