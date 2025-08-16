import os
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from tasks import start_multi_split_job, get_job_status, get_job_result
from utils import allowed_file, unique_safe_filename, is_safe_output

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    if "files" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = unique_safe_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            saved_files.append(filepath)
        else:
            return jsonify({"error": "Apenas PDFs são permitidos"}), 400

    job_id = start_multi_split_job(saved_files, app.config["OUTPUT_FOLDER"])
    return jsonify({"job_id": job_id}), 202

@app.route("/status/<job_id>")
def status(job_id):
    status = get_job_status(job_id)
    if not status:
        return jsonify({"error": "Job não encontrado"}), 404
    return jsonify(status)

@app.route("/download/<job_id>")
def download(job_id):
    zip_path = get_job_result(job_id)
    if not zip_path or not os.path.exists(zip_path):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    if not is_safe_output(zip_path, app.config["OUTPUT_FOLDER"]):
        return jsonify({"error": "Acesso não permitido"}), 403
    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
