import time
from pathlib import Path
from config import UPLOAD_FOLDER, OUTPUT_FOLDER, LOG_FOLDER

def cleanup_old_files(max_age_hours: int = 12):
    cutoff = time.time() - max_age_hours * 3600
    for folder in (UPLOAD_FOLDER, OUTPUT_FOLDER, LOG_FOLDER):
        for path in folder.glob("**/*"):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
            except Exception:
                pass
