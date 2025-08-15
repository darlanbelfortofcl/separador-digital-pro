import os, uuid
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS, OUTPUT_FOLDER

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def unique_safe_filename(filename: str) -> str:
    fname = secure_filename(filename)
    base, ext = os.path.splitext(fname)
    return f"{base}_{uuid.uuid4().hex}{ext}"

def safe_basename(filename: str) -> str:
    fname = secure_filename(filename)
    base, _ = os.path.splitext(fname)
    return base or "arquivo"

def zip_tree(tree_root: Path, zip_path: Path) -> Path:
    tree_root = Path(tree_root)
    zip_path = Path(zip_path)
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(tree_root):
            for f in files:
                fp = Path(root) / f
                arc = fp.relative_to(tree_root)
                zf.write(fp, arcname=str(arc))
    return zip_path

def is_safe_output(path: Path) -> bool:
    try:
        path = Path(path).resolve()
        return OUTPUT_FOLDER.resolve() in path.parents or path == OUTPUT_FOLDER.resolve()
    except Exception:
        return False
