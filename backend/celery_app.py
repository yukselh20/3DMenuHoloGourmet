import os
from celery import Celery
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables to ensure broker URL is available
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# The .env file should contain:
# CELERY_BROKER_URL='redis://localhost:6379/0'

celery_broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')

# Create Celery instance
celery = Celery(
    "tasks",
    broker=celery_broker_url,
    backend=celery_broker_url, # Using redis as backend to store results if needed
    include=["tasks"] # List of modules to import when the worker starts
)

celery.conf.update(
    task_track_started=True,
)