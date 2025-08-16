
import os, uuid
from werkzeug.utils import secure_filename

def allowed_file(filename: str, allowed_exts: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_exts

def unique_safe_filename(original_name: str) -> str:
    safe = secure_filename(original_name) or "arquivo.pdf"
    base, ext = os.path.splitext(safe)
    if ext.lower() != ".pdf":
        ext = ".pdf"
    return f"{base}_{uuid.uuid4().hex[:8]}{ext}"

def is_safe_output(path: str, base_dir: str) -> bool:
    base = os.path.realpath(base_dir)
    target = os.path.realpath(path)
    return os.path.commonpath([base, target]) == base
