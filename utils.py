import os
import uuid

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def unique_safe_filename(filename):
    name, ext = os.path.splitext(filename)
    return f"{name}_{uuid.uuid4().hex}{ext}"

def is_safe_output(path, base_folder):
    abs_base = os.path.abspath(base_folder)
    abs_path = os.path.abspath(path)
    return abs_path.startswith(abs_base)
