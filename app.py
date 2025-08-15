from flask import Flask, render_template, request, Response, jsonify, send_file
import json
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename

from config import (
    UPLOAD_FOLDER, OUTPUT_FOLDER, MAX_CONTENT_LENGTH,
    DEFAULT_HOST, DEFAULT_PORT
)
from file_utils import allowed_file, unique_filename, zip_dir, is_safe_output_path
from jobs import job_queues, get_logger, start_thread, sse_stream
from pdf_ops import split_pdf
from conversor import convert_pdf_to_docx, convert_docx_to_pdf
from cleanup import start_cleanup_scheduler


app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Inicia o agendador de limpeza
_scheduler = start_cleanup_scheduler()


# ===== Workers =====

def _worker_split(job_id: str, pdf_path: Path, qualidade: str, timeout: int, threads: int, limpar: bool):
    q = job_queues[job_id]
    log = get_logger(job_id)
    try:
        base = pdf_path.stem
        pasta_destino = OUTPUT_FOLDER / f"{base}_paginas"
        pasta_otimizada = pasta_destino / "otimizados"
        pasta_destino.mkdir(parents=True, exist_ok=True)
        pasta_otimizada.mkdir(parents=True, exist_ok=True)

        q.put({"stage": "start", "msg": "Iniciando separação…", "atual": 0, "total": 100})

        def cb(nome, atual, total):
            try:
                pct = int((atual / total) * 100) if total else 0
            except Exception:
                pct = 0
            q.put({"stage": "progress", "msg": f"{nome}: Página {atual}/{total}", "atual": pct, "total": 100})

        split_pdf(pdf_path, pasta_destino, pasta_otimizada, limpar=limpar, callback=cb)

        zip_name = OUTPUT_FOLDER / f"{base}_paginas.zip"
        zip_dir(pasta_destino, zip_name)

        q.put({
            "done": True,
            "msg": "Separação concluída ✅",
            "atual": 100,
            "total": 100,
            "download": str(zip_name)
        })
        log.info("Split finalizado: %s", zip_name)
    except Exception as e:
        log.exception("Erro no split")
        q.put({"error": True, "msg": f"Erro: {e}"})
        q.put({"done": True})


def _worker_convert(job_id: str, src_path: Path, mode: str):
    q = job_queues[job_id]
    log = get_logger(job_id)
    try:
        base = src_path.stem
        q.put({"stage": "start", "msg": "Preparando conversão (modo turbo editável)…", "atual": 1, "total": 100})

        if mode == "pdf2docx":
            out_path = OUTPUT_FOLDER / f"{base}.docx"

            def cb(pct, msg=None):
                payload = {"stage": "progress", "atual": int(pct), "total": 100}
                if msg:
                    payload["msg"] = msg
                q.put(payload)

            convert_pdf_to_docx(src_path, out_path, turbo=True, callback=cb)
        elif mode == "docx2pdf":
            out_path = OUTPUT_FOLDER / f"{base}.pdf"
            convert_docx_to_pdf(src_path, out_path)
        else:
            raise ValueError("Modo inválido")

        q.put({"done": True, "msg": "Conversão concluída ✅", "atual": 100, "total": 100, "download": str(out_path)})
        log.info("Conversão concluída: %s -> %s", src_path, out_path)
    except Exception as e:
        log.exception("Erro na conversão")
        q.put({"error": True, "msg": f"Erro na conversão: {e}"})
        q.put({"done": True})


# ===== Rotas =====

@app.route("/")
def home():
    return render_template("index.html") if app.jinja_env.loader else "OK"


@app.route("/converter")
def pagina_converter():
    return render_template("converter.html") if app.jinja_env.loader else "converter"


@app.route("/dividir")
def pagina_dividir():
    return render_template("dividir.html") if app.jinja_env.loader else "dividir"


@app.route("/convert", methods=["POST"])
def convert():
    mode = request.form.get("mode")
    file = request.files.get("arquivo")

    if mode not in ("pdf2docx", "docx2pdf"):
        return jsonify({"ok": False, "error": "Modo inválido."}), 400

    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Selecione um arquivo."}), 400

    if not allowed_file(file.filename):
        return jsonify({"ok": False, "error": "Extensão não permitida. Use PDF ou DOCX."}), 400

    from werkzeug.utils import secure_filename
    safe_name = secure_filename(file.filename)
    filename = unique_filename(safe_name)
    src_path = (UPLOAD_FOLDER / filename)
    file.save(src_path)

    job_id = uuid.uuid4().hex
    start_thread(_worker_convert, (job_id, src_path, mode))

    return jsonify({"ok": True, "job_id": job_id})


@app.route("/process", methods=["POST"])
def process():
    qualidade = request.form.get("qualidade", "ebook")
    timeout = int(request.form.get("timeout", 60))
    threads = int(request.form.get("threads", 4))
    limpar = "limpar" in request.form
    arquivo_pdf = request.files.get("arquivo_pdf")

    if not arquivo_pdf or not arquivo_pdf.filename:
        return jsonify({"ok": False, "error": "Selecione um arquivo PDF."}), 400

    if not allowed_file(arquivo_pdf.filename) or not arquivo_pdf.filename.lower().endswith(".pdf"):
        return jsonify({"ok": False, "error": "Envie um PDF válido."}), 400

    from werkzeug.utils import secure_filename
    safe_name = secure_filename(arquivo_pdf.filename)
    filename = unique_filename(safe_name)
    caminho_pdf = (UPLOAD_FOLDER / filename)
    arquivo_pdf.save(caminho_pdf)

    job_id = uuid.uuid4().hex
    start_thread(_worker_split, (job_id, caminho_pdf, qualidade, timeout, threads, limpar))

    return jsonify({"ok": True, "job_id": job_id})


@app.route("/stream")
def stream():
    job_id = request.args.get("job")
    if not job_id:
        return Response("job inválido\n", status=400)
    return Response(sse_stream(job_id), mimetype="text/event-stream")


@app.route("/download")
def download():
    path = request.args.get("path")
    if not path:
        return "Arquivo não encontrado", 404

    candidate = Path(path)
    if not candidate.exists() or not is_safe_output_path(candidate):
        return "Arquivo não encontrado", 404

    return send_file(candidate, as_attachment=True)


if __name__ == "__main__":
    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT)
