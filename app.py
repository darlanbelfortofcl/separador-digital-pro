import os
import uuid
import threading
import time
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, Response, abort
from werkzeug.utils import secure_filename
from utils import split_pdf_with_progress, allowed_file
from io import BytesIO

app = Flask(__name__, static_url_path="/static", static_folder="app/static", template_folder="app/templates")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

LOGIN_USER = os.getenv("LOGIN_USER", "lucyta")
LOGIN_PASS = os.getenv("LOGIN_PASS", "29031984bB@G")

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

PROGRESS = {}
RESULTS = {}

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = request.form.get("usuario", "").strip()
        pwd = request.form.get("senha", "").strip()
        if user == LOGIN_USER and pwd == LOGIN_PASS:
            session["logged_in"] = True
            return redirect(url_for("painel"))
        else:
            error = "Usuário ou senha inválidos."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/painel", methods=["GET"])
@login_required
def painel():
    return render_template("index.html")

@app.route("/processar", methods=["POST"])
@login_required
def processar():
    if "pdf" not in request.files:
        return jsonify({"ok": False, "msg": "Nenhum arquivo enviado."}), 400
    file = request.files["pdf"]
    if file.filename == "":
        return jsonify({"ok": False, "msg": "Selecione um arquivo PDF."}), 400

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return jsonify({"ok": False, "msg": "Arquivo inválido. Envie um PDF."}), 400

    job_id = str(uuid.uuid4())
    PROGRESS[job_id] = {"percent": 0, "status": "Iniciando...", "filename": filename}
    RESULTS.pop(job_id, None)

    save_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")
    file.save(save_path)

    ranges = request.form.get("paginas", "").strip()
    def worker():
        try:
            out_zip_path = os.path.join(OUTPUT_FOLDER, f"{job_id}_split.zip")
            split_pdf_with_progress(
                input_path=save_path,
                output_zip_path=out_zip_path,
                progress_callback=lambda p, s: PROGRESS[job_id].update({"percent": p, "status": s}),
                ranges=ranges or None
            )
            PROGRESS[job_id]["percent"] = 100
            PROGRESS[job_id]["status"] = "Concluído"
            RESULTS[job_id] = out_zip_path
        except Exception as e:
            PROGRESS[job_id]["status"] = f"Erro: {e}"
            PROGRESS[job_id]["percent"] = 0

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok": True, "job_id": job_id})

@app.route("/eventos/<job_id>")
@login_required
def eventos(job_id):
    def stream():
        while True:
            if job_id not in PROGRESS:
                yield "event: error\ndata: Job não encontrado\n\n"
                break
            data = PROGRESS[job_id]
            percent = int(data.get("percent", 0))
            status = data.get("status", "")
            payload = {"percent": percent, "status": status}
            yield f"data: {payload}\n\n"
            if percent >= 100 and job_id in RESULTS:
                download_url = url_for("baixar", job_id=job_id)
                payload_done = {"percent": 100, "status": "Concluído", "download": download_url}
                yield f"data: {payload_done}\n\n"
                break
            time.sleep(0.5)
    return Response(stream(), mimetype="text/event-stream")

@app.route("/baixar/<job_id>")
@login_required
def baixar(job_id):
    if job_id not in RESULTS:
        abort(404)
    path = RESULTS[job_id]
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))

@app.route("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
