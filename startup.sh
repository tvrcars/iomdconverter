#!/bin/bash
apt-get update && apt-get install -y libgl1-mesa-glx
gunicorn --bind=0.0.0.0:8000 app:app 