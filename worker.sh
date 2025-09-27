#!/usr/bin/env bash
set -e

# Start Xvfb too, if worker tasks use Selenium
Xvfb :99 -screen 0 1280x1024x24 -ac &
export DISPLAY=:99

# Run Celery worker
exec celery -A tasks worker --loglevel=info --concurrency=1
