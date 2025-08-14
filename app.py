
from flask import Flask, render_template, request, Response, jsonify, send_file
import os, logging, threading, queue, json, uuid, zipfile, time
from werkzeug.utils import secure_filename
from conversor import convert_pdf_to_docx, convert_docx_to_pdf

app = Flask(__name__, static_folder="static", template_folder="templates")
logging.basicConfig(filename="processamento.log", level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

job_queues = {}

def _worker_convert(job_id, src_path, mode):
    q = job_queues[job_id]
    try:
        base, ext = os.path.splitext(os.path.basename(src_path))
        q.put({"stage":"start","msg":"Preparando conversão…","atual":1,"total":100})

        stop_flag = {"stop": False}
        def heartbeat():
            pct = 1
            while not stop_flag["stop"]:
                pct = min(95, pct + 2)
                q.put({"stage":"progress","msg":"Convertendo…","atual":pct,"total":100})
                time.sleep(1.0)
        hb = threading.Thread(target=heartbeat, daemon=True)
        hb.start()

        if mode == "pdf2docx":
            out_path = os.path.join(OUTPUT_FOLDER, f"{base}.docx")
            convert_pdf_to_docx(src_path, out_path)
        elif mode == "docx2pdf":
            out_path = os.path.join(OUTPUT_FOLDER, f"{base}.pdf")
            convert_docx_to_pdf(src_path, out_path)
        else:
            raise ValueError("Modo inválido")

        stop_flag["stop"] = True
        q.put({"done": True, "msg": "Conversão concluída ✅", "atual":100, "total":100, "download": out_path})
    except Exception as e:
        q.put({"error": True, "msg": f"Erro na conversão: {e}"})
        q.put({"done": True})

# Split worker (placeholder simple to keep package self-contained)
def _worker_split(job_id, pdf_path):
    q = job_queues[job_id]
    try:
        # For simplicity in this demo: just return the PDF as 'zip' (placeholder)
        # In your real project, plug your existing 'processar_pdf' here.
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        zip_name = os.path.join(OUTPUT_FOLDER, f"{base}.zip")
        import zipfile
        with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(pdf_path, os.path.basename(pdf_path))
        q.put({"done": True, "msg":"Separação concluída ✅ (demo)","atual":100,"total":100,"download":zip_name})
    except Exception as e:
        q.put({"error": True, "msg": f"Erro: {e}"}); q.put({"done": True})

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
    arquivo_pdf = request.files.get("arquivo_pdf")
    if not arquivo_pdf or not arquivo_pdf.filename:
        return jsonify({"ok": False, "error": "Selecione um arquivo PDF."}), 400
    filename = secure_filename(arquivo_pdf.filename)
    caminho_pdf = os.path.join(UPLOAD_FOLDER, filename)
    arquivo_pdf.save(caminho_pdf)

    job_id = uuid.uuid4().hex
    q = queue.Queue()
    job_queues[job_id] = q
    t = threading.Thread(target=_worker_split, args=(job_id, caminho_pdf), daemon=True)
    t.start()
    return jsonify({"ok": True, "job_id": job_id})

@app.route("/stream")
def stream():
    job_id = request.args.get("job")
    if not job_id or job_id not in job_queues:
        return Response("job inválido\n", status=400)
    q = job_queues[job_id]
    def event_stream():
        done = False; last_ping = time.time()
        while not done:
            try:
                item = q.get(timeout=2)
                if isinstance(item, dict):
                    if item.get("done"): done = True
                    yield "data: " + json.dumps(item, ensure_ascii=False) + "\n\n"
            except queue.Empty:
                if time.time()-last_ping > 5:
                    yield ": keep-alive\n\n"; last_ping = time.time()
        job_queues.pop(job_id, None)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/download")
def download():
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return "Arquivo não encontrado", 404
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
