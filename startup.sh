#!/bin/bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0 --timeout 600 --workers 1 --threads 2 app:app
