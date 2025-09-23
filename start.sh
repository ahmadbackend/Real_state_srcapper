#!/usr/bin/env bash
set -e

# start virtual X server on :99 (so Chrome can be "headful")
Xvfb :99 -screen 0 1280x1024x24 -ac &

export DISPLAY=:99

# Start uvicorn — Render sets $PORT for your service, fallback to 8000 locally
exec uvicorn Nigerian_urls:app --host 0.0.0.0 --port ${PORT:-8000} 
