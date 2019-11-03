#!/bin/bash
pushd /home/bart/sites/recognizeme
source venv/bin/activate
python -m facerecognition -c config/api.prod.yml
popd
