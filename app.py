
import os
import threading
import uuid
from flask import Flask, request, jsonify, send_file, render_template, abort
from werkzeug.utils import secure_filename
from tasks import process_job_thread
from utils import allowed_file, unique_safe_filename, is_safe_output

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
ALLOWED_EXTENSIONS = {"pdf"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB por requisição

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Armazena o estado dos jobs em memória
JOBS = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    if "files" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    files = request.files.getlist("files")
    files = [f for f in files if f and allowed_file(f.filename, ALLOWED_EXTENSIONS)]
    if not files:
        return jsonify({"error": "Envie ao menos um PDF válido"}), 400

    job_id = uuid.uuid4().hex
    job_upload_dir = os.path.join(UPLOAD_FOLDER, job_id)
    job_output_dir = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(job_upload_dir, exist_ok=True)
    os.makedirs(job_output_dir, exist_ok=True)

    saved_files = []
    for file in files:
        filename = unique_safe_filename(file.filename)
        filepath = os.path.join(job_upload_dir, filename)
        file.save(filepath)
        saved_files.append(filepath)

    # Inicializa estado do job
    JOBS[job_id] = {"status": "queued", "progress": 0, "result": None, "files": []}

    # Inicia thread de processamento
    th = threading.Thread(target=process_job_thread, args=(job_id, saved_files, job_output_dir, JOBS), daemon=True)
    th.start()

    return jsonify({"job_id": job_id}), 202

@app.route("/status/<job_id>")
def status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job não encontrado"}), 404
    resp = {"status": job["status"], "progress": job.get("progress", 0)}
    if job["status"] == "finished":
        resp["download_url"] = f"/download/{job_id}"
    if job.get("errors"):
        resp["errors"] = job["errors"]
    return jsonify(resp)

@app.route("/list/<job_id>")
def list_files(job_id):
    job = JOBS.get(job_id)
    if not job or job["status"] != "finished":
        return jsonify({"error": "Ainda não disponível"}), 404
    # retorna lista de arquivos individuais
    return jsonify({"files": job.get("files", [])})

@app.route("/download/<job_id>")
def download_zip(job_id):
    zip_path = os.path.join(OUTPUT_FOLDER, job_id, "pdfs_divididos.zip")
    if not (os.path.exists(zip_path) and is_safe_output(zip_path, OUTPUT_FOLDER)):
        return jsonify({"error": "Arquivo não disponível"}), 404
    return send_file(zip_path, as_attachment=True, download_name="pdfs_divididos.zip")

@app.route("/download/<job_id>/<path:filename>")
def download_single(job_id, filename):
    # baixa um arquivo individual do job
    base_dir = os.path.join(OUTPUT_FOLDER, job_id)
    file_path = os.path.join(base_dir, filename)
    if not (os.path.exists(file_path) and is_safe_output(file_path, base_dir)):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    return send_file(file_path, as_attachment=True, download_name=filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
