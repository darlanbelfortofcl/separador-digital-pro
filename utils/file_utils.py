import os, uuid, mimetypes
from pathlib import Path
try:
    import magic  # python-magic (libmagic)
    HAVE_MAGIC = True
except Exception:
    HAVE_MAGIC = False

from werkzeug.utils import secure_filename
from config import ALLOWED_EXT

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def detect_mime(path: Path) -> str:
    if HAVE_MAGIC:
        try:
            m = magic.Magic(mime=True)
            return m.from_file(str(path))
        except Exception:
            pass
    # fallback
    ctype, _ = mimetypes.guess_type(str(path))
    return ctype or "application/octet-stream"

def is_pdf(path: Path) -> bool:
    mime = detect_mime(path)
    return mime in ("application/pdf", "application/x-pdf", "application/octet-stream") and path.suffix.lower() == ".pdf"

def unique_safe_filename(name: str) -> str:
    safe = secure_filename(name)
    base, ext = os.path.splitext(safe)
    return f"{base}_{uuid.uuid4().hex}{ext}"

def safe_stem(name: str) -> str:
    safe = secure_filename(name)
    base, _ = os.path.splitext(safe)
    return base or "arquivo"
