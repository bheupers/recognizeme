#!/usr/bin/env bash
rsync -avz --exclude venv --exclude dlib-19.18 --exclude .git --exclude .idea --exclude '*__pycache__*' . bart-jetson:sites/recognizeme/
