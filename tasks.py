
import os
import zipfile
from PyPDF2 import PdfReader, PdfWriter

def process_job_thread(job_id: str, input_files: list[str], output_dir: str, JOBS: dict):
    try:
        JOBS[job_id]["status"] = "started"
        total_pages = 0
        for f in input_files:
            try:
                reader = PdfReader(f)
                total_pages += len(reader.pages)
            except Exception:
                pass

        done = 0
        out_files = []

        for f in input_files:
            base = os.path.splitext(os.path.basename(f))[0]
            try:
                reader = PdfReader(f)
                for i, page in enumerate(reader.pages, start=1):
                    writer = PdfWriter()
                    writer.add_page(page)
                    out_name = f"{base}_pagina_{i}.pdf"
                    out_path = os.path.join(output_dir, out_name)
                    with open(out_path, "wb") as out_f:
                        writer.write(out_f)
                    out_files.append(out_name)
                    done += 1
                    if total_pages:
                        JOBS[job_id]["progress"] = int((done / total_pages) * 100)
            except Exception:
                errs = JOBS[job_id].get("errors", [])
                errs.append(base)
                JOBS[job_id]["errors"] = errs

        # cria zip final
        zip_path = os.path.join(output_dir, "pdfs_divididos.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for name in out_files:
                full = os.path.join(output_dir, name)
                if os.path.exists(full):
                    z.write(full, arcname=name)

        JOBS[job_id]["files"] = out_files
        JOBS[job_id]["status"] = "finished"
        JOBS[job_id]["progress"] = 100
        JOBS[job_id]["result"] = zip_path
    except Exception:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["progress"] = 0
