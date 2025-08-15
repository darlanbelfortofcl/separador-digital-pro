import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
LOG_FOLDER = BASE_DIR / "logs"

for d in (UPLOAD_FOLDER, OUTPUT_FOLDER, LOG_FOLDER):
    d.mkdir(parents=True, exist_ok=True)

# Flask
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

# Celery & Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

# Validation
ALLOWED_EXT = {"pdf"}
MAX_FILE_MB = None  # sem limite
