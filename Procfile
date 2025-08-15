# Render/Heroku-style process types
# web process is required by Render Web Service
web: gunicorn src.app:app
# worker process for Celery (create a separate Background Worker on Render)
worker: celery -A src.jobs.celery worker --loglevel=info
