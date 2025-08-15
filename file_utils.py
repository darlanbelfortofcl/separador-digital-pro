import os
import uuid
import time
from pathlib import Path
from typing import Tuple
from zipfile import ZipFile, ZIP_DEFLATED

from config import OUTPUT_FOLDER, ALLOWED_EXTENSIONS, UPLOAD_FOLDER


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_filename(original_name: str) -> str:
    base, ext = os.path.splitext(original_name)
    return f"{base}_{uuid.uuid4().hex}{ext}"


def zip_dir(src_dir: Path, zip_path: Path) -> Path:
    src_dir = Path(src_dir)
    zip_path = Path(zip_path)
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for f in files:
                fp = Path(root) / f
                rel = fp.relative_to(src_dir)
                zf.write(fp, arcname=str(rel))
    return zip_path


def is_safe_output_path(path: Path) -> bool:
    """Garante que o caminho do download aponte para dentro de OUTPUT_FOLDER."""
    try:
        path = Path(path).resolve()
        return OUTPUT_FOLDER.resolve() in path.parents or path == OUTPUT_FOLDER.resolve()
    except Exception:
        return False


def remove_older_than(dir_path: Path, age_hours: int) -> int:
    """Remove arquivos de dir_path com mtime mais antigo que age_hours. Retorna quantidade removida."""
    cutoff = time.time() - age_hours * 3600
    removed = 0
    dir_path = Path(dir_path)
    if not dir_path.exists():
        return 0
    for root, dirs, files in os.walk(dir_path):
        for name in files:
            fp = Path(root) / name
            try:
                if fp.stat().st_mtime < cutoff:
                    fp.unlink(missing_ok=True)
                    removed += 1
            except Exception:
                pass
        # remove diretórios vazios
        for d in list(dirs):
            dp = Path(root) / d
            try:
                if not any(dp.iterdir()):
                    dp.rmdir()
            except Exception:
                pass
    return removed
