# backend/app/worker/celery_app.py
import os
from celery import Celery
from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "arbitrage_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Optional configuration settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Automatically look for tasks inside app.worker.tasks
    include=["app.worker.tasks"]
)

celery_app.conf.beat_schedule = {
    'run-all-active-configs-every-15-mins': {
        'task': 'app.worker.tasks.run_all_configs', # We will create this task next
        'schedule': crontab(minute='*/15'), # Runs every 15 minutes
    },
}