from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
LOG_FOLDER = BASE_DIR / "logs"

for p in (UPLOAD_FOLDER, OUTPUT_FOLDER, LOG_FOLDER):
    p.mkdir(parents=True, exist_ok=True)

# Apenas PDFs
ALLOWED_EXTENSIONS = {"pdf"}

# Servidor
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
