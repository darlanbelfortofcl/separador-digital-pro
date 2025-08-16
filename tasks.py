import os
import uuid
import zipfile
from PyPDF2 import PdfReader, PdfWriter

jobs = {}

def start_multi_split_job(files, output_folder):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "em fila", "progress": 0, "result": None}
    try:
        output_files = []
        for file in files:
            reader = PdfReader(file)
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                out_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(file))[0]}_page_{i+1}.pdf")
                with open(out_path, "wb") as f_out:
                    writer.write(f_out)
                output_files.append(out_path)

        zip_path = os.path.join(output_folder, f"{job_id}.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for f in output_files:
                zipf.write(f, os.path.basename(f))

        jobs[job_id] = {"status": "concluído", "progress": 100, "result": zip_path}
    except Exception as e:
        jobs[job_id] = {"status": "erro", "progress": 0, "result": None}
    return job_id

def get_job_status(job_id):
    return jobs.get(job_id)

def get_job_result(job_id):
    job = jobs.get(job_id)
    if job and job["status"] == "concluído":
        return job["result"]
    return None
