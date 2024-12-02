#!/bin/bash
apt-get update
apt-get install -y libgl1-mesa-glx
pip install -r requirements.txt
gunicorn --bind=0.0.0.0 --timeout 600 app:app
