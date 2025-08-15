from flask import Flask, request, jsonify, send_file, render_template
from pathlib import Path
import uuid

from config import UPLOAD_FOLDER, OUTPUT_FOLDER, HOST, PORT, MAX_CONTENT_LENGTH, DEBUG
from file_utils import allowed_file, unique_safe_filename, is_safe_output
from jobs import start_multi_split_job, jobs

app = Flask(__name__, template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/split")
def split():
    files = request.files.getlist("arquivos")
    if not files:
        return jsonify({"ok": False, "error": "Envie pelo menos um PDF no campo 'arquivos'."}), 400
    saved_paths = []
    orig_names = []
    for f in files:
        if not f or not f.filename:
            continue
        if not allowed_file(f.filename):
            return jsonify({"ok": False, "error": f"Extensão não permitida: {f.filename}"}), 400
        fname = unique_safe_filename(f.filename)
        dest = UPLOAD_FOLDER / fname
        f.save(dest)
        saved_paths.append(dest)
        orig_names.append(f.filename)
    if not saved_paths:
        return jsonify({"ok": False, "error": "Nenhum PDF válido foi enviado."}), 400
    job_id = uuid.uuid4().hex
    start_multi_split_job(job_id, saved_paths, orig_names)
    return jsonify({"ok": True, "job_id": job_id})

@app.get("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job não encontrado"}), 404
    return jsonify({"ok": True, "job": job})

@app.get("/download")
def download():
    from urllib.parse import unquote
    path = Path(unquote(request.args.get("path", "")))
    if not path.exists() or not is_safe_output(path):
        return "Arquivo não encontrado", 404
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
