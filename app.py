
from flask import Flask, render_template, request, Response, jsonify
import os, logging, threading, queue, json, uuid
from werkzeug.utils import secure_filename
from processador import processar_pdf

app = Flask(__name__)
logging.basicConfig(filename="processamento.log", level=logging.INFO, format="%(levelname)s:%(message)s")

job_queues = {}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def _start_worker(job_id, arquivos_pdf, qualidade, timeout, threads, limpar, pasta_destino, pasta_otimizada):
    q = job_queues[job_id]
    def callback(nome, atual, total):
        q.put({"msg": f"{nome}: Página {atual}/{total}", "arquivo": nome, "atual": atual, "total": total})
    try:
        for pdf in arquivos_pdf:
            processar_pdf(pdf, pasta_destino, pasta_otimizada, qualidade, timeout, limpar, threads, callback=callback)
        q.put({"done": True, "msg": "Processamento concluído ✅"})
    except Exception as e:
        q.put({"error": True, "msg": f"Erro: {e}"})
    finally:
        q.put({"done": True})

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

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
    arquivos_pdf = [caminho_pdf]

    base_destino = os.path.join(UPLOAD_FOLDER, os.path.splitext(filename)[0] + "_paginas_individuais")
    pasta_destino = base_destino
    pasta_otimizada = os.path.join(base_destino, "otimizados")
    os.makedirs(pasta_destino, exist_ok=True)
    os.makedirs(pasta_otimizada, exist_ok=True)

    job_id = uuid.uuid4().hex
    q = queue.Queue()
    job_queues[job_id] = q

    t = threading.Thread(target=_start_worker, args=(job_id, arquivos_pdf, qualidade, timeout, threads, limpar, pasta_destino, pasta_otimizada), daemon=True)
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
    app.run(debug=True, threaded=True)
