#!/bin/bash
cd /home/bart/sites/recognizeme
source venv/bin/activate
exec python -m facerecognition -c config/api.prod.yml
