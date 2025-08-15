from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    worker_send_task_events=True,
    task_track_started=True,
)
