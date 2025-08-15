import threading
from pathlib import Path
from typing import List, Dict
from pdf_ops import split_pdf_to_folder
from file_utils import safe_basename, zip_tree
from config import OUTPUT_FOLDER

jobs: Dict[str, dict] = {}

def start_multi_split_job(job_id: str, pdfs: List[Path], original_names: List[str]):
    jobs[job_id] = {"status": "running", "progress": 0, "total": len(pdfs), "zip": None, "details": []}
    def run():
        try:
            root_out = OUTPUT_FOLDER / job_id
            root_out.mkdir(exist_ok=True)
            for idx, (pdf_path, orig_name) in enumerate(zip(pdfs, original_names), start=1):
                base = safe_basename(orig_name)
                target_dir = root_out / base
                written = split_pdf_to_folder(pdf_path, target_dir, base_name=base)
                jobs[job_id]["details"].append({"original": orig_name, "folder": str(target_dir), "pages": len(written)})
                jobs[job_id]["progress"] = idx
            zip_path = OUTPUT_FOLDER / f"{job_id}.zip"
            zip_tree(root_out, zip_path)
            jobs[job_id]["zip"] = str(zip_path)
            jobs[job_id]["status"] = "done"
        except Exception as e:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)
    threading.Thread(target=run, daemon=True).start()
