from flask import Flask, render_template, request, jsonify, send_file, url_for
from pathlib import Path
import threading, time, os
from .config import UPLOAD_FOLDER, OUTPUT_FOLDER, HOST, PORT, DEBUG, CLEANUP_INTERVAL_MINUTES
from .jobs import task_split, task_merge, task_compress, task_pdf_to_docx, celery
from .utils import allowed_file, unique_safe_filename, is_pdf

# Flask app configured to serve /static at /static even with package layout
app = Flask(__name__, template_folder='templates', static_folder='../static', static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

@app.context_processor
def inject_urls():
    return dict(static_url=url_for("static", filename=""))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/converter')
def converter():
    return render_template('converter.html')

def _save_uploads(files):
    saved = []
    for f in files:
        if not f or not f.filename:
            continue
        if not allowed_file(f.filename):
            raise ValueError(f"Extensão não permitida: {f.filename}")
        safe = unique_safe_filename(f.filename)
        dest = UPLOAD_FOLDER / safe
        f.save(dest)
        if not is_pdf(dest):
            dest.unlink(missing_ok=True)
            raise ValueError(f"Arquivo inválido (não é PDF real): {f.filename}")
        saved.append((dest, f.filename))
    if not saved:
        raise ValueError("Nenhum arquivo válido enviado.")
    return saved

@app.post('/api/split')
def api_split():
    files = request.files.getlist('arquivos')
    try:
        saved = _save_uploads(files)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400
    path, original = saved[0]
    res = task_split.delay(str(path), original)
    return jsonify(ok=True, task_id=res.id)

@app.post('/api/merge')
def api_merge():
    files = request.files.getlist('arquivos')
    try:
        saved = _save_uploads(files)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400
    paths = [str(p) for p,_ in saved]
    res = task_merge.delay(paths)
    return jsonify(ok=True, task_id=res.id)

@app.post('/api/compress')
def api_compress():
    files = request.files.getlist('arquivos')
    if not files or len(files)!=1:
        return jsonify(ok=False, error='Envie apenas um PDF para compressão.'), 400
    try:
        saved = _save_uploads(files)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400
    path, _ = saved[0]
    res = task_compress.delay(str(path))
    return jsonify(ok=True, task_id=res.id)

@app.post('/api/pdf-to-docx')
def api_pdf_to_docx():
    files = request.files.getlist('arquivos')
    ocr = request.form.get('ocr') == 'on'
    if not files or len(files)!=1:
        return jsonify(ok=False, error='Envie apenas um PDF para conversão.'), 400
    try:
        saved = _save_uploads(files)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400
    path, _ = saved[0]
    res = task_pdf_to_docx.delay(str(path), ocr=ocr)
    return jsonify(ok=True, task_id=res.id)

@app.get('/api/status/<task_id>')
def api_status(task_id):
    r = celery.AsyncResult(task_id)
    state = r.state
    payload = dict(state=state)
    if state == 'SUCCESS':
        payload['result'] = r.get()
    elif state == 'FAILURE':
        payload['error'] = str(r.info)
    return jsonify(ok=True, **payload)

@app.get('/download')
def download():
    p = Path(request.args.get('path',''))
    if not p.exists() or not p.is_file():
        return 'Arquivo não encontrado', 404
    return send_file(p, as_attachment=True)

def _cleanup_worker(interval_min):
    while True:
        now = time.time()
        for folder in (UPLOAD_FOLDER, OUTPUT_FOLDER):
            for f in folder.glob('**/*'):
                try:
                    if f.is_file():
                        age_min = (now - f.stat().st_mtime)/60
                        if age_min > (interval_min*24/24):  # same minutes
                            f.unlink(missing_ok=True)
                except Exception:
                    pass
        time.sleep(interval_min*60)

def start_cleanup_thread():
    t = threading.Thread(target=_cleanup_worker, args=(CLEANUP_INTERVAL_MINUTES,), daemon=True)
    t.start()

start_cleanup_thread()

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
