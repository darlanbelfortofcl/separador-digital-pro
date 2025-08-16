from pathlib import Path
from werkzeug.utils import secure_filename

def allowed_file(filename: str, allowed={"pdf"}) -> bool:
    return "." in filename and filename.rsplit(".",1)[1].lower() in allowed

def save_upload(file_storage, dest_dir: Path) -> Path:
    fname = secure_filename(file_storage.filename)
    dest = dest_dir / fname
    file_storage.save(dest)
    return dest
