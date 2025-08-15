import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
OUTPUT_FOLDER = BASE_DIR / 'outputs'
LOG_FOLDER = BASE_DIR / 'logs'
for d in (UPLOAD_FOLDER, OUTPUT_FOLDER, LOG_FOLDER):
    d.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.environ.get('SECRET_KEY','dev-secret')
HOST=os.environ.get('HOST','0.0.0.0')
PORT=int(os.environ.get('PORT',5000))
DEBUG=os.environ.get('FLASK_DEBUG','0')=='1'
REDIS_URL=os.environ.get('REDIS_URL')
CLEANUP_INTERVAL_MINUTES=int(os.environ.get('CLEANUP_INTERVAL_MINUTES','30'))
ALLOWED_EXT={'pdf'}
MAX_FILE_MB=None
