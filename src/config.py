import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
for d in (UPLOAD_FOLDER, OUTPUT_FOLDER):
    d.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.environ.get("SECRET_KEY","dev-secret")
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 1024 * 1024 * 512))  # 512MB
ALLOWED_EXTENSIONS = {"pdf"}

HOST = os.environ.get("HOST","0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_DEBUG","0") == "1"
