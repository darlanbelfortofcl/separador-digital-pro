from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
LOG_FOLDER = BASE_DIR / "logs"

for p in (UPLOAD_FOLDER, OUTPUT_FOLDER, LOG_FOLDER):
    p.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf"}
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 400 * 1024 * 1024))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
