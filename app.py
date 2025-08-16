from flask import Flask, request, jsonify, send_file
import os, uuid, threading, time, logging
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime, timedelta

# Configurações
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
LOG_FOLDER = "logs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB limite

# Logging
logger = logging.getLogger("separador")
handler = logging.FileHandler(os.path.join(LOG_FOLDER, "app.log"))
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Helpers
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def looks_like_pdf(file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except:
        return False

def unique_safe_filename(original_name: str) -> str:
    safe = secure_filename(original_name) or "arquivo.pdf"
    base, ext = os.path.splitext(safe)
    if ext.lower() != ".pdf":
        ext = ".pdf"
    uniq = uuid.uuid4().hex[:10]
    return f"{base}_{uniq}{ext}"

def is_safe_output(base_dir: str, path: str) -> bool:
    base = os.path.realpath(base_dir)
    target = os.path.realpath(path)
    return os.path.commonpath([base, target]) == base

# Rotas
@app.route("/split", methods=["POST"])
def split_pdf():
    if "files" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    files = [f for f in request.files.getlist("files") if f and allowed_file(f.filename)]
    if not files:
        return jsonify({"error": "Envie pelo menos 1 PDF válido"}), 400

    results = []
    for file in files:
        try:
            safe_name = unique_safe_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, safe_name)
            file.save(input_path)

            if not looks_like_pdf(input_path):
                os.remove(input_path)
                results.append({"name": file.filename, "error": "Arquivo não parece ser PDF"})
                continue

            # Dividir PDF
            reader = PdfReader(input_path)
            output_files = []
            for i, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)
                out_name = f"{os.path.splitext(safe_name)[0]}_pagina_{i}.pdf"
                out_path = os.path.join(OUTPUT_FOLDER, out_name)
                with open(out_path, "wb") as out_f:
                    writer.write(out_f)
                output_files.append(out_name)

            results.append({"name": file.filename, "pages": len(output_files), "outputs": output_files})

        except Exception as e:
            logger.error("Erro ao processar %s: %s", file.filename, e, exc_info=True)
            results.append({"name": file.filename, "error": "Falha ao processar PDF"})

    return jsonify(results)

@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not (os.path.exists(file_path) and is_safe_output(OUTPUT_FOLDER, file_path)):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    return send_file(file_path, as_attachment=True)

# Cleanup thread
def cleanup_loop(base_dirs=(UPLOAD_FOLDER, OUTPUT_FOLDER), ttl_hours=12):
    ttl = timedelta(hours=ttl_hours)
    while True:
        cutoff = datetime.now() - ttl
        for base in base_dirs:
            for root, _, files in os.walk(base):
                for f in files:
                    p = os.path.join(root, f)
                    try:
                        if datetime.fromtimestamp(os.path.getmtime(p)) < cutoff:
                            os.remove(p)
                    except:
                        pass
            for root, dirs, _ in os.walk(base, topdown=False):
                for d in dirs:
                    dp = os.path.join(root, d)
                    try:
                        if not os.listdir(dp):
                            os.rmdir(dp)
                    except:
                        pass
        time.sleep(3600)

threading.Thread(target=cleanup_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)
