import os
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
LOG_FOLDER = BASE_DIR / "logs"

# Criação de pastas
for p in (UPLOAD_FOLDER, OUTPUT_FOLDER, LOG_FOLDER):
    p.mkdir(parents=True, exist_ok=True)

# Uploads
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 200 * 1024 * 1024))  # 200 MB por padrão

# SSE / Jobs
QUEUE_GET_TIMEOUT = int(os.environ.get("QUEUE_GET_TIMEOUT", 5))

# Limpeza automática
CLEANUP_ENABLED = os.environ.get("CLEANUP_ENABLED", "1") == "1"
CLEANUP_AGE_HOURS = int(os.environ.get("CLEANUP_AGE_HOURS", 24))  # apaga arquivos com mais de 24h
CLEANUP_INTERVAL_MINUTES = int(os.environ.get("CLEANUP_INTERVAL_MINUTES", 30))  # frequência do job

# App
DEFAULT_HOST = os.environ.get("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
