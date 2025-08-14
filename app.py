import os, logging, threading, queue, json, uuid
from flask import Flask, render_template, request, Response, jsonify, send_file
from werkzeug.utils import secure_filename
from processador import split_pdf_all, split_pdf_by_ranges, split_pdf_by_pages, compress_pdf
from conversor import CONVERSION_FUNCTIONS

# --- Configuração básica ---
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB
ALLOWED_UPLOADS = {".pdf",".docx",".txt",".xlsx",".csv",".pptx",".jpg",".jpeg",".png",".odt"}

logging.basicConfig(filename="processamento.log", level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

job_queues = {}
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def _allowed(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_UPLOADS

# ---------- Workers ----------
def _worker_convert(job_id, src_path, mode):
    q = job_queues[job_id]
    try:
        if mode not in CONVERSION_FUNCTIONS:
            raise ValueError("Modo de conversão inválido.")
        nome = os.path.basename(src_path)
        base, _ = os.path.splitext(nome)
        # ext_out baseado no mode (depois do '2'), porém alguns modos têm sufixo especial
        ext_out = mode.split("2")[-1].replace("_ocr","")
        out_path = os.path.join(OUTPUT_FOLDER, f"{base}.{ext_out}")
        q.put({"msg": f"Iniciando conversão: {nome}", "atual": 5, "total": 100})
        CONVERSION_FUNCTIONS[mode](src_path, out_path)
        q.put({"msg": "Finalizando…", "atual": 95, "total": 100})
        q.put({"done": True, "msg": "Conversão concluída ✅", "atual": 100, "total": 100, "download": out_path})
    except Exception as e:
        q.put({"error": True, "msg": f"Erro na conversão: {e}"})
    finally:
        q.put({"done": True})

def _worker_split(job_id, src_path, mode, payload):
    q = job_queues[job_id]
    try:
        base = os.path.splitext(os.path.basename(src_path))[0]
        destino = os.path.join(OUTPUT_FOLDER, f"{base}_paginas")
        os.makedirs(destino, exist_ok=True)
        def cb(atual, total):
            q.put({"msg": f"Página {atual}/{total}", "atual": atual, "total": total})
        if mode == "all":
            split_pdf_all(src_path, destino, callback=cb)
        elif mode == "ranges":
            ranges = payload.get("ranges","").strip()
            split_pdf_by_ranges(src_path, destino, ranges, callback=cb)
        elif mode == "pages":
            pages = payload.get("pages","").strip()
            split_pdf_by_pages(src_path, destino, pages, callback=cb)
        else:
            raise ValueError("Modo de divisão inválido.")
        q.put({"done": True, "msg": "Divisão concluída ✅", "download_dir": destino})
    except Exception as e:
        q.put({"error": True, "msg": f"Erro na divisão: {e}"})
    finally:
        q.put({"done": True})

def _worker_compress(job_id, src_path, quality):
    q = job_queues[job_id]
    try:
        base = os.path.splitext(os.path.basename(src_path))[0]
        out_path = os.path.join(OUTPUT_FOLDER, f"{base}_compressed.pdf")
        q.put({"msg": "Comprimindo…", "atual": 10, "total": 100})
        compress_pdf(src_path, out_path, quality=quality, progress=lambda p: q.put({"msg":"Processando…","atual":p,"total":100}))
        q.put({"done": True, "msg": "Compressão concluída ✅", "atual": 100, "total": 100, "download": out_path})
    except Exception as e:
        q.put({"error": True, "msg": f"Erro na compressão: {e}"})
    finally:
        q.put({"done": True})

# ---------- Rotas ----------
@app.route("/")
def index():
    return render_template("index.html")

def _save_upload(file):
    if not file or not file.filename:
        raise ValueError("Nenhum arquivo enviado.")
    if not _allowed(file.filename):
        raise ValueError("Extensão de arquivo não permitida.")
    filename = secure_filename(file.filename)
    unique = uuid.uuid4().hex[:8] + "_" + filename
    src_path = os.path.join(UPLOAD_FOLDER, unique)
    file.save(src_path)
    return src_path

@app.route("/convert", methods=["POST"])
def convert():
    mode = request.form.get("mode","").strip()
    file = request.files.get("arquivo")
    try:
        src_path = _save_upload(file)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    job_id = uuid.uuid4().hex
    q = queue.Queue()
    job_queues[job_id] = q
    t = threading.Thread(target=_worker_convert, args=(job_id, src_path, mode), daemon=True)
    t.start()
    return jsonify({"ok": True, "job_id": job_id})

@app.route("/pdf/split", methods=["POST"])
def pdf_split():
    mode = request.form.get("mode","all")
    file = request.files.get("arquivo_pdf")
    payload = {
        "ranges": request.form.get("ranges",""),
        "pages": request.form.get("pages",""),
    }
    try:
        src_path = _save_upload(file)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    job_id = uuid.uuid4().hex
    q = queue.Queue()
    job_queues[job_id] = q
    t = threading.Thread(target=_worker_split, args=(job_id, src_path, mode, payload), daemon=True)
    t.start()
    return jsonify({"ok": True, "job_id": job_id})

@app.route("/pdf/compress", methods=["POST"])
def pdf_compress():
    quality = request.form.get("quality","medium")
    file = request.files.get("arquivo_pdf")
    try:
        src_path = _save_upload(file)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    job_id = uuid.uuid4().hex
    q = queue.Queue()
    job_queues[job_id] = q
    t = threading.Thread(target=_worker_compress, args=(job_id, src_path, quality), daemon=True)
    t.start()
    return jsonify({"ok": True, "job_id": job_id})

@app.route("/download")
def download():
    path = request.args.get("path")
    if not path:
        return "Arquivo não encontrado", 404
    abs_output = os.path.abspath(OUTPUT_FOLDER)
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(abs_output) or not os.path.exists(abs_path):
        return "Arquivo não encontrado", 404
    return send_file(abs_path, as_attachment=True)

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
                item = q.get(timeout=10)
                if item.get("done"):
                    done = True
                yield "data: " + json.dumps(item, ensure_ascii=False) + "\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"
        try:
            del job_queues[job_id]
        except KeyError:
            pass
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
