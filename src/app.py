from flask import Flask, render_template, request, send_file, jsonify, abort
from pathlib import Path
import io, zipfile, traceback, os

from . import config
from .utils import allowed_file, save_upload
from .pdf_ops import split_pdf, merge_pdfs, validate_pdf
from .doc_ops import pdf_to_docx_editable

app = Flask(__name__, static_folder=str(Path(__file__).resolve().parent.parent / 'static'), template_folder='templates')
app.config.from_object(config)

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/health')
def health():
    return jsonify(status='ok')

@app.post('/api/split')
def api_split():
    if 'files' not in request.files:
        abort(400, 'Envie 1 ou mais PDFs')
    files = request.files.getlist('files')
    if not files:
        abort(400, 'Envie 1 ou mais PDFs')

    out_zip_buf = io.BytesIO()
    with zipfile.ZipFile(out_zip_buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files:
            if not f.filename or not allowed_file(f.filename):
                continue
            pdf_path = save_upload(f, config.UPLOAD_FOLDER)
            try:
                parts = split_pdf(pdf_path, config.OUTPUT_FOLDER / pdf_path.stem)
                for p in parts:
                    z.write(p, arcname=f"{pdf_path.stem}/{p.name}")
            except Exception:
                traceback.print_exc()
                continue
    out_zip_buf.seek(0)
    return send_file(out_zip_buf, as_attachment=True, download_name='pdfs_divididos.zip')

@app.post('/api/merge')
def api_merge():
    if 'files' not in request.files:
        abort(400, 'Envie 2 ou mais PDFs')
    files = request.files.getlist('files')
    paths = []
    for f in files:
        if f and allowed_file(f.filename):
            p = save_upload(f, config.UPLOAD_FOLDER)
            paths.append(p)
    if len(paths) < 2:
        abort(400, 'Envie ao menos 2 PDFs')
    out_path = config.OUTPUT_FOLDER / 'mesclado.pdf'
    merge_pdfs(paths, out_path)
    return send_file(out_path, as_attachment=True, download_name='mesclado.pdf')

@app.post('/api/convert')
def api_convert():
    if 'file' not in request.files:
        abort(400, 'Envie 1 PDF')
    f = request.files['file']
    if not f or not allowed_file(f.filename):
        abort(400, 'Arquivo inválido')
    pdf_path = save_upload(f, config.UPLOAD_FOLDER)
    try:
        validate_pdf(pdf_path)
    except Exception as e:
        abort(400, f'PDF inválido: {e}')
    out_path = config.OUTPUT_FOLDER / f"{pdf_path.stem}.docx"
    pdf_to_docx_editable(pdf_path, out_path)
    return send_file(out_path, as_attachment=True, download_name=f"{pdf_path.stem}.docx")

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
