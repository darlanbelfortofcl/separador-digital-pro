web: gunicorn app:app
worker: celery -A celery_app.celery worker --loglevel=INFO
