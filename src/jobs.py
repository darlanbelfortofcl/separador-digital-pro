from . import config
try:
    if config.REDIS_URL:
        from celery import Celery
        celery = Celery('tasks', broker=config.REDIS_URL, backend=config.REDIS_URL)
    else:
        celery = None
except Exception:
    celery = None
