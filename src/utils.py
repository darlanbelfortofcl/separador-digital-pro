import os, io, mimetypes
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app

try:
    import magic  # python-magic
    _HAS_MAGIC = True
except Exception:
    _HAS_MAGIC = False

def allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", {"pdf"})

def detect_mime(path: Path) -> str:
    # Prefer libmagic if available; fallback to mimetypes
    if _HAS_MAGIC:
        try:
            ms = magic.Magic(mime=True)
            return ms.from_file(str(path))
        except Exception:
            pass
    guess, _ = mimetypes.guess_type(path.name)
    return guess or "application/octet-stream"

def save_upload(file_storage, dest_dir: Path) -> Path:
    fname = secure_filename(file_storage.filename)
    dest = dest_dir / fname
    file_storage.save(dest)
    return dest
