import os, logging, threading, time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, url_for
from .config import UPLOAD_FOLDER, OUTPUT_FOLDER, HOST, PORT, DEBUG, CLEANUP_INTERVAL_MINUTES, LOG_FOLDER
from .utils import allowed_file, unique_safe_filename, validate_pdf, json_log, request_id
from .jobstore import JobStore
from . import jobs as J
from pythonjsonlogger import jsonlogger
handler=logging.StreamHandler(); formatter=jsonlogger.JsonFormatter('%(levelname)s %(message)s %(asctime)s'); handler.setFormatter(formatter)
logging.getLogger().handlers=[handler]; logging.getLogger().setLevel(logging.INFO)
log=logging.getLogger(__name__)
STATIC_PATH=(Path(__file__).resolve().parent.parent / 'static').resolve()
app=Flask(__name__, template_folder='templates', static_folder=str(STATIC_PATH), static_url_path='/static')
app.config['SECRET_KEY']=os.environ.get('SECRET_KEY','dev-secret')
store=JobStore(LOG_FOLDER / 'jobstore.json')
@app.after_request
def add_headers(resp): resp.headers['X-Request-ID']=request_id(); return resp
@app.context_processor
def inject_urls(): return dict(static_url=url_for('static', filename=''))
@app.get('/health')
def health(): return {'ok':True, 'celery_enabled': bool(J.CELERY_ENABLED)}
@app.get('/health/queue')
def health_queue(): return {'celery_enabled': bool(J.CELERY_ENABLED)}
@app.route('/')
def index(): return render_template('index.html')
@app.route('/converter')
def converter(): return render_template('converter.html')
def _save_uploads(files):
    saved=[]
    for f in files:
        if not f or not f.filename: continue
        if not allowed_file(f.filename): raise ValueError(f'Extensão não permitida: {f.filename}')
        safe=unique_safe_filename(f.filename); dest=UPLOAD_FOLDER / safe; f.save(dest); meta=validate_pdf(dest); saved.append((dest, f.filename, meta))
    if not saved: raise ValueError('Nenhum arquivo válido enviado.')
    return saved
def _eta_meta(meta):
    pages=meta.get('pages',1); seconds=max(1, J._eta_by_pages(pages)) if hasattr(J,'_eta_by_pages') else 2
    return dict(eta_seconds=seconds, pages=pages)
@app.post('/api/split')
def api_split():
    rid=request_id()
    files=request.files.getlist('arquivos')
    try:
        saved=_save_uploads(files); path, original, meta=saved[0]
    except Exception as e:
        json_log('upload_error', request_id=rid, error=str(e)); return jsonify(ok=False, error=str(e)), 400
    if J.CELERY_ENABLED and J.celery:
        res=J.task_split.delay(str(path), original); store.put(res.id, dict(op='split', file=str(path), original=original, meta=meta))
        return jsonify(ok=True, task_id=res.id, **_eta_meta(meta))
    else:
        out=J.run_split_sync(str(path), original); return jsonify(ok=True, path=out, **_eta_meta(meta))
@app.post('/api/merge')
def api_merge():
    rid=request_id(); files=request.files.getlist('arquivos')
    try:
        saved=_save_uploads(files); paths=[str(p) for p,_,_ in saved]; meta={'pages':2*len(paths)}
    except Exception as e:
        json_log('upload_error', request_id=rid, error=str(e)); return jsonify(ok=False, error=str(e)), 400
    if J.CELERY_ENABLED and J.celery:
        res=J.task_merge.delay(paths); store.put(res.id, dict(op='merge', files=paths, out='merged.pdf', meta=meta)); return jsonify(ok=True, task_id=res.id, **_eta_meta(meta))
    else:
        out=J.run_merge_sync(paths); return jsonify(ok=True, path=out, **_eta_meta(meta))
@app.post('/api/compress')
def api_compress():
    rid=request_id(); files=request.files.getlist('arquivos')
    if not files or len(files)!=1: return jsonify(ok=False, error='Envie apenas um PDF para compressão.'), 400
    try:
        saved=_save_uploads(files); path, _, meta=saved[0]
    except Exception as e:
        json_log('upload_error', request_id=rid, error=str(e)); return jsonify(ok=False, error=str(e)), 400
    if J.CELERY_ENABLED and J.celery:
        res=J.task_compress.delay(str(path)); store.put(res.id, dict(op='compress', file=str(path), meta=meta)); return jsonify(ok=True, task_id=res.id, **_eta_meta(meta))
    else:
        out=J.run_compress_sync(str(path)); return jsonify(ok=True, path=out, **_eta_meta(meta))
@app.post('/api/pdf-to-docx')
def api_pdf_to_docx():
    rid=request_id(); files=request.files.getlist('arquivos')
    if not files or len(files)!=1: return jsonify(ok=False, error='Envie apenas um PDF para conversão.'), 400
    try:
        saved=_save_uploads(files); path, _, meta=saved[0]
    except Exception as e:
        json_log('upload_error', request_id=rid, error=str(e)); return jsonify(ok=False, error=str(e)), 400
    if J.CELERY_ENABLED and J.celery:
        res=J.task_pdf_to_docx.delay(str(path)); store.put(res.id, dict(op='pdf_to_docx', file=str(path), meta=meta)); return jsonify(ok=True, task_id=res.id, **_eta_meta(meta))
    else:
        out=J.run_pdf_to_docx_sync(str(path)); return jsonify(ok=True, path=out, **_eta_meta(meta))
@app.get('/api/status/<task_id>')
def api_status(task_id):
    if not (J.CELERY_ENABLED and J.celery): return jsonify(ok=False, error='Fila assíncrona desativada.'), 400
    r=J.celery.AsyncResult(task_id); state=r.state; payload=dict(state=state)
    if state=='SUCCESS': payload['result']=r.get()
    elif state=='FAILURE': payload['error']=str(r.info)
    return jsonify(ok=True, **payload)
@app.post('/api/retry/<task_id>')
def api_retry(task_id):
    if not (J.CELERY_ENABLED and J.celery): return jsonify(ok=False, error='Fila assíncrona desativada.'), 400
    payload=store.get(task_id)
    if not payload: return jsonify(ok=False, error='Tarefa desconhecida.'), 404
    op=payload['op']
    if op=='split': res=J.task_split.delay(payload['file'], payload.get('original', 'arquivo.pdf'))
    elif op=='merge': res=J.task_merge.delay(payload['files'])
    elif op=='compress': res=J.task_compress.delay(payload['file'])
    elif op=='pdf_to_docx': res=J.task_pdf_to_docx.delay(payload['file'])
    else: return jsonify(ok=False, error='Operação não suportada.'), 400
    return jsonify(ok=True, task_id=res.id)
@app.get('/download')
def download():
    p=Path(request.args.get('path',''))
    if not p.exists() or not p.is_file(): return 'Arquivo não encontrado', 404
    return send_file(p, as_attachment=True)
def _cleanup_worker(interval_min:int):
    while True:
        now=time.time()
        for folder in (UPLOAD_FOLDER, OUTPUT_FOLDER):
            for f in folder.glob('**/*'):
                try:
                    if f.is_file() and (now - f.stat().st_mtime)/60 > interval_min: f.unlink(missing_ok=True)
                except Exception: pass
        time.sleep(interval_min*60)
def start_cleanup_thread():
    t=threading.Thread(target=_cleanup_worker, args=(CLEANUP_INTERVAL_MINUTES,), daemon=True); t.start()
start_cleanup_thread()
if __name__=='__main__': app.run(host=HOST, port=PORT, debug=DEBUG)
