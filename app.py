
from flask import Flask, render_template, request, Response, jsonify, send_file
import os, logging, threading, queue, json, uuid, zipfile, sys
from werkzeug.utils import secure_filename
from processador import processar_pdf
from conversor import convert_pdf_to_docx, convert_docx_to_pdf

app = Flask(__name__, static_folder="static", template_folder="templates")

logging.basicConfig(filename="processamento.log", level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

job_queues = {}

def _worker_split(job_id, pdf_path, qualidade="ebook", timeout=60, threads=4, limpar=False):
    q = job_queues[job_id]
    try:
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        pasta_destino = os.path.join(OUTPUT_FOLDER, f"{base}_paginas")
        pasta_otimizada = os.path.join(pasta_destino, "otimizados")
        os.makedirs(pasta_destino, exist_ok=True)
        os.makedirs(pasta_otimizada, exist_ok=True)

        q.put({"stage":"start", "msg":"Iniciando separação…", "atual":0, "total":100})

        def cb(nome, atual, total):
            try:
                pct = int((atual/total)*100) if total else 0
            except Exception:
                pct = 0
            q.put({"stage":"progress","msg":f"{nome}: Página {atual}/{total}", "atual":pct, "total":100})

        processar_pdf(pdf_path, pasta_destino, pasta_otimizada, qualidade=qualidade, timeout=timeout, limpar=limpar, threads=threads, callback=cb)

        zip_name = os.path.join(OUTPUT_FOLDER, f"{base}_paginas.zip")
        with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
            for rootp, _, files in os.walk(pasta_destino):
                for f in files:
                    fp = os.path.join(rootp, f)
                    rel = os.path.relpath(fp, pasta_destino)
                    zf.write(fp, rel)

        q.put({"done": True, "msg": "Separação concluída ✅", "atual":100, "total":100, "download": zip_name})
    except Exception as e:
        q.put({"error": True, "msg": f"Erro: {e}"})
        q.put({"done": True})

def _worker_convert(job_id, src_path, mode):
    q = job_queues[job_id]
    try:
        base, ext = os.path.splitext(os.path.basename(src_path))
        q.put({"stage":"start","msg":"Preparando conversão (modo turbo editável)…","atual":1,"total":100})

        if mode == "pdf2docx":
            out_path = os.path.join(OUTPUT_FOLDER, f"{base}.docx")
            def cb(pct, msg=None):
                payload = {"stage":"progress", "atual": int(pct), "total":100}
                if msg: payload["msg"] = msg
                q.put(payload)
            convert_pdf_to_docx(src_path, out_path, turbo=True, callback=cb)
        elif mode == "docx2pdf":
            out_path = os.path.join(OUTPUT_FOLDER, f"{base}.pdf")
            convert_docx_to_pdf(src_path, out_path)
        else:
            raise ValueError("Modo inválido")

        q.put({"done": True, "msg": "Conversão concluída ✅", "atual":100, "total":100, "download": out_path})
    except Exception as e:
        q.put({"error": True, "msg": f"Erro na conversão: {e}"})
        q.put({"done": True})

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/converter")
def pagina_converter():
    return render_template("converter.html")

@app.route("/dividir")
def pagina_dividir():
    return render_template("dividir.html")

@app.route("/convert", methods=["POST"])
def convert():
    mode = request.form.get("mode")
    file = request.files.get("arquivo")
    if mode not in ("pdf2docx", "docx2pdf"):
        return jsonify({"ok": False, "error": "Modo inválido."}), 400
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Selecione um arquivo."}), 400

    filename = secure_filename(file.filename)
    src_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(src_path)

    job_id = uuid.uuid4().hex
    q = queue.Queue()
    job_queues[job_id] = q
    t = threading.Thread(target=_worker_convert, args=(job_id, src_path, mode), daemon=True)
    t.start()

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

    filename = secure_filename(arquivo_pdf.filename)
    caminho_pdf = os.path.join(UPLOAD_FOLDER, filename)
    arquivo_pdf.save(caminho_pdf)

    job_id = uuid.uuid4().hex
    q = queue.Queue()
    job_queues[job_id] = q
    t = threading.Thread(target=_worker_split, args=(job_id, caminho_pdf, qualidade, timeout, threads, limpar), daemon=True)
    t.start()

    return jsonify({"ok": True, "job_id": job_id})

@app.route("/stream")
def stream():
    job_id = request.args.get("job")
    if not job_id or job_id not in job_queues:
        return Response("job inválido\n", status=400)

    q = job_queues[job_id]

    def event_stream():
        done = False
        while not done:
            try:
                item = q.get(timeout=5)
                if isinstance(item, dict):
                    if item.get("done"):
                        done = True
                    yield "data: " + json.dumps(item, ensure_ascii=False) + "\n\n"
            except queue.Empty:
                yield ": ping\n\n"
        job_queues.pop(job_id, None)

    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/download")
def download():
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return "Arquivo não encontrado", 404
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
