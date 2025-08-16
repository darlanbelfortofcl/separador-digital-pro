import os, time, uuid
from collections import deque
from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, send_file, jsonify, Response, abort
from werkzeug.utils import secure_filename
from .utils import parse_ranges, split_pdf_to_disk, zip_paths

bp = Blueprint("main", __name__)

# Rate limiting de login (5/min por IP)
LOGIN_WINDOW = 60  # segundos
MAX_ATTEMPTS = 5
login_attempts = {}  # ip -> deque[timestamps]

def _allow_login(ip: str) -> bool:
    now = time.time()
    dq = login_attempts.setdefault(ip, deque())
    # remove itens fora da janela
    while dq and now - dq[0] > LOGIN_WINDOW:
        dq.popleft()
    return len(dq) < MAX_ATTEMPTS

def _register_attempt(ip: str):
    now = time.time()
    dq = login_attempts.setdefault(ip, deque())
    dq.append(now)

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logado"):
            return redirect(url_for("main.login"))
        return fn(*args, **kwargs)
    return wrapper

@bp.route("/", methods=["GET"])
def root():
    return redirect(url_for("main.login"))

@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
        if not _allow_login(ip):
            error = "Muitas tentativas. Aguarde 1 minuto."
        else:
            senha = request.form.get("senha", "")
            if senha and senha == os.getenv("SENHA_ADMIN", "admin"):
                session["logado"] = True
                return redirect(url_for("main.painel"))
            else:
                _register_attempt(ip)
                error = "Senha inválida."
    return render_template("login.html", error=error)

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@bp.route("/painel")
@login_required
def painel():
    return render_template("painel.html")

# Memória simples de progresso/resultado (em memória, leve para Render free)
PROGRESS = {}
RESULTS = {}
PREVIEW_FILES = {}  # job_id -> {page:int -> file_path}

@bp.route("/processar", methods=["POST"])
@login_required
def processar():
    if "pdf" not in request.files:
        return jsonify({"ok": False, "msg": "Nenhum arquivo enviado."}), 400
    f = request.files["pdf"]
    if not f.filename:
        return jsonify({"ok": False, "msg": "Selecione um arquivo PDF."}), 400

    filename = secure_filename(f.filename)
    if not filename.lower().endswith(".pdf"):
        return jsonify({"ok": False, "msg": "Envie um PDF."}), 400

    job_id = uuid.uuid4().hex
    PROGRESS[job_id] = {"percent": 0, "status": "Iniciando..."}
    RESULTS.pop(job_id, None)
    PREVIEW_FILES[job_id] = {}

    up_dir = current_app.config["UPLOAD_FOLDER"]
    out_dir = current_app.config["OUTPUT_FOLDER"]
    os.makedirs(up_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    saved_pdf = os.path.join(up_dir, f"{job_id}_{filename}")
    f.save(saved_pdf)

    ranges = (request.form.get("paginas") or "").strip()

    def worker():
        try:
            from PyPDF2 import PdfReader
            total = len(PdfReader(saved_pdf).pages)
            pages = parse_ranges(ranges, total_pages=total)
            PROGRESS[job_id].update({"percent": 2, "status": f"Lendo documento ({total} páginas)…"})

            # dividir e salvar páginas em disco (para preview e zip)
            pages_dir = os.path.join(out_dir, job_id, "pages")
            saved = split_pdf_to_disk(saved_pdf, pages_dir, pages)
            file_paths = [path for _, path in saved]

            # atualizar progresso incremental
            for i, (_p, _path) in enumerate(saved, start=1):
                pct = int(i * 98 / max(1, len(saved)))
                PROGRESS[job_id].update({"percent": pct, "status": f"Processando {i}/{len(saved)}…"})
                PREVIEW_FILES[job_id][_p] = _path

            # zip pronto
            zip_path = os.path.join(out_dir, job_id, f"{os.path.splitext(filename)[0]}_split.zip")
            os.makedirs(os.path.dirname(zip_path), exist_ok=True)
            zip_paths(file_paths, zip_path)
            RESULTS[job_id] = zip_path
            PROGRESS[job_id].update({"percent": 100, "status": "Concluído"})
        except Exception as e:
            PROGRESS[job_id].update({"percent": 0, "status": f"Erro: {e}"})
    import threading
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok": True, "job_id": job_id})

@bp.route("/eventos/<job_id>")
@login_required
def eventos(job_id):
    def stream():
        last = None
        while True:
            data = PROGRESS.get(job_id)
            if not data:
                yield "event: error\ndata: Job não encontrado\n\n"
                break
            if data != last:
                # enviar JSON simples
                import json as _json
                yield "data: " + _json.dumps(data, ensure_ascii=False) + "\n\n"
                last = dict(data)
            if data.get("percent", 0) >= 100 and job_id in RESULTS:
                # envia URL de download
                import json as _json
                payload_done = {"percent": 100, "status": "Concluído", "download": url_for('main.baixar', job_id=job_id)}
                yield "data: " + _json.dumps(payload_done, ensure_ascii=False) + "\n\n"
                break
            time.sleep(0.4)
    return Response(stream(), mimetype="text/event-stream")

@bp.route("/baixar/<job_id>")
@login_required
def baixar(job_id):
    path = RESULTS.get(job_id)
    if not path or not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))

@bp.route("/preview/<job_id>/<int:page>")
@login_required
def preview(job_id, page):
    # Serve a página isolada como "preview" (miniatura é simulada via CSS scale no front)
    page_map = PREVIEW_FILES.get(job_id, {})
    fp = page_map.get(page)
    if not fp or not os.path.exists(fp):
        abort(404)
    return send_file(fp, as_attachment=False, download_name=os.path.basename(fp))
