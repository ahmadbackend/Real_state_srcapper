from celery import Celery, signals
import os, requests
from utils_neigeria import all_pages_looping as neigeria_scraper

# Redis from Render (set in env)
redis_url = os.getenv("REDIS_URL", "redis://host.docker.internal:6379/0")

celery_app = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url
)

WEBHOOK_NEIGERIA_URL = os.getenv("N8N_NIGERIAN_HOOK_URL")  # n8n webhook URL from Render env

@celery_app.task
def run_scraper_neigeria(query: str, max_pages):
    return neigeria_scraper(query, max_pages)

# Send webhook to n8n when task finishes successfully
@signals.task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    if WEBHOOK_NEIGERIA_URL:
        try:
            requests.post(WEBHOOK_NEIGERIA_URL, json={
                "task_id": sender.request.id,
                "status": "SUCCESS",
                "result": result,
            }, timeout=10)
        except Exception as e:
            print(f"Webhook error: {e}")


# Send webhook to n8n if task fails
@signals.task_failure.connect
def task_failure_handler(sender=None, exception=None, **kwargs):
    if WEBHOOK_NEIGERIA_URL:
        try:
            requests.post(WEBHOOK_NEIGERIA_URL, json={
                "task_id": sender.request.id,
                "status": "FAILURE",
                "error": str(exception),
            }, timeout=10)
        except Exception as e:
            print(f"Webhook error: {e}")
