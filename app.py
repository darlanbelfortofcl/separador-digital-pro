
import os, io, time, threading, queue, json, platform, uuid
from flask import Flask, render_template, request, jsonify, send_file, Response, url_for
from werkzeug.utils import secure_filename
from pdf2docx import Converter
from PyPDF2 import PdfReader, PdfWriter, PdfMerger

UPLOAD = "uploads"
OUTPUT = "outputs"
app = Flask(__name__)
os.makedirs(UPLOAD, exist_ok=True); os.makedirs(OUTPUT, exist_ok=True)

progress_channels = {}
def sse_stream(task_id):
    q = progress_channels.get(task_id)
    last = time.time()
    def _e(d): return f"data: {json.dumps(d)}\n\n"
    yield _e({"message":"Iniciando...", "progress":0})
    while True:
        if time.time()-last>5:
            last=time.time(); yield _e({"keepalive":True})
        try: item=q.get(timeout=1)
        except: continue
        if item is None: break
        yield _e(item)
        if item.get("done"): break

def put_progress(tid, **data):
    q=progress_channels.get(tid)
    if q: q.put(data)
def close_progress(tid):
    q=progress_channels.get(tid)
    if q: q.put(None)
def make_task():
    tid=uuid.uuid4().hex; progress_channels[tid]=queue.Queue(); return tid
def allow_docx_to_pdf():
    return platform.system().lower() in ("windows","darwin")
def cleanup(path):
    try:
        if os.path.exists(path): os.remove(path)
    except: pass

@app.route("/")
def home(): return render_template("index.html")

@app.route("/converter")
def converter_page(): return render_template("converter.html", docx2pdf_enabled=allow_docx_to_pdf())

@app.route("/dividir")
def dividir_page(): return render_template("dividir.html")
@app.route("/mesclar")
def mesclar_page(): return render_template("mesclar.html")
@app.route("/extrair")
def extrair_page(): return render_template("extrair.html")
@app.route("/comprimir")
def comprimir_page(): return render_template("comprimir.html")

@app.post("/api/pdf2docx")
def api_pdf2docx():
    f=request.files.get("file")
    if not f or f.filename=="": return jsonify({"ok":False,"error":"Nenhum arquivo enviado."}),400
    name=secure_filename(f.filename)
    if not name.lower().endswith(".pdf"): return jsonify({"ok":False,"error":"Envie um PDF."}),400
    in_path=os.path.join(UPLOAD, uuid.uuid4().hex+"_"+name); f.save(in_path)
    out_name=os.path.splitext(os.path.basename(name))[0]+".docx"
    out_path=os.path.join(OUTPUT, uuid.uuid4().hex+"_"+out_name)
    tid=make_task()
    def worker():
        try:
            reader=PdfReader(in_path); total=len(reader.pages)
            cv=Converter(in_path)
            try:
                cv.convert(out_path, start=0, end=None, layout_mode="loose")  # TURBO + EDITÁVEL
            finally:
                cv.close()
            for i in range(total):
                put_progress(tid, progress=int((i+1)/total*100), message=f"Convertendo página {i+1}/{total}..."); time.sleep(0.005)
            put_progress(tid, progress=100, message="Conversão concluída.", done=True, download=url_for('download', path=os.path.basename(out_path)))
        except Exception as e:
            put_progress(tid, error=str(e), done=True)
        finally:
            close_progress(tid); cleanup(in_path)
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok":True,"progress_url":url_for("progress",task_id=tid)})

@app.post("/api/docx2pdf")
def api_docx2pdf():
    if not allow_docx_to_pdf(): return jsonify({"ok":False,"error":"DOCX→PDF não suportado neste servidor."}),400
    f=request.files.get("file")
    if not f or f.filename=="": return jsonify({"ok":False,"error":"Nenhum arquivo enviado."}),400
    name=secure_filename(f.filename)
    if not name.lower().endswith((".docx",".doc")): return jsonify({"ok":False,"error":"Envie um DOCX."}),400
    in_path=os.path.join(UPLOAD, uuid.uuid4().hex+"_"+name); f.save(in_path)
    out_path=os.path.join(OUTPUT, uuid.uuid4().hex+"_"+os.path.splitext(os.path.basename(name))[0]+".pdf")
    tid=make_task()
    def worker():
        try:
            from docx2pdf import convert as d2p
            put_progress(tid, progress=10, message="Preparando conversão...")
            d2p(in_path, out_path)
            put_progress(tid, progress=100, message="Conversão concluída.", done=True, download=url_for('download', path=os.path.basename(out_path)))
        except Exception as e:
            put_progress(tid, error=str(e), done=True)
        finally:
            close_progress(tid); cleanup(in_path)
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok":True,"progress_url":url_for("progress",task_id=tid)})

@app.post("/api/split")
def api_split():
    f=request.files.get("file")
    if not f or f.filename=="": return jsonify({"ok":False,"error":"Nenhum arquivo enviado."}),400
    name=secure_filename(f.filename)
    if not name.lower().endswith(".pdf"): return jsonify({"ok":False,"error":"Envie um PDF."}),400
    in_path=os.path.join(UPLOAD, uuid.uuid4().hex+"_"+name); f.save(in_path)
    tid=make_task()
    def worker():
        try:
            reader=PdfReader(in_path); total=len(reader.pages); paths=[]
            for i in range(total):
                w=PdfWriter(); w.add_page(reader.pages[i])
                out=os.path.join(OUTPUT, f"{uuid.uuid4().hex}_page_{i+1}.pdf")
                with open(out,"wb") as fp: w.write(fp)
                paths.append(out); put_progress(tid, progress=int((i+1)/total*100), message=f"Gerando página {i+1}/{total}...")
            import zipfile
            zip_path=os.path.join(OUTPUT, f"split_{uuid.uuid4().hex}.zip")
            with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
                for p in paths: z.write(p, os.path.basename(p).split('_',1)[-1])
            put_progress(tid, progress=100, message="Divisão concluída.", done=True, download=url_for('download', path=os.path.basename(zip_path)))
        except Exception as e:
            put_progress(tid, error=str(e), done=True)
        finally:
            close_progress(tid); 
            try:
                os.remove(in_path)
            except: pass
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok":True,"progress_url":url_for("progress",task_id=tid)})

@app.post("/api/merge")
def api_merge():
    f=request.files.get("file"); extras=request.files.getlist("extra")
    if not f and not extras: return jsonify({"ok":False,"error":"Envie pelo menos um PDF."}),400
    files=[]
    for up in ([f]+extras) if f else extras:
        if up and up.filename:
            name=secure_filename(up.filename)
            if not name.lower().endswith(".pdf"): return jsonify({"ok":False,"error":f"Arquivo inválido: {name}"}),400
            path=os.path.join(UPLOAD, uuid.uuid4().hex+'_'+name); up.save(path); files.append(path)
    tid=make_task()
    def worker():
        try:
            merger=PdfMerger(); total=len(files)
            for i,p in enumerate(files,1):
                merger.append(p); put_progress(tid, progress=int(i/total*100), message=f"Adicionando {i}/{total}...")
            out=os.path.join(OUTPUT, f"merged_{uuid.uuid4().hex}.pdf")
            with open(out,"wb") as fp: merger.write(fp)
            merger.close()
            put_progress(tid, progress=100, message="Mesclagem concluída.", done=True, download=url_for('download', path=os.path.basename(out)))
        except Exception as e:
            put_progress(tid, error=str(e), done=True)
        finally:
            close_progress(tid); 
            for p in files:
                try: os.remove(p)
                except: pass
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok":True,"progress_url":url_for("progress",task_id=tid)})

@app.post("/api/extract")
def api_extract():
    f=request.files.get("file")
    if not f or f.filename=="": return jsonify({"ok":False,"error":"Nenhum arquivo enviado."}),400
    ranges=(request.form.get("ranges") or "").strip()
    name=secure_filename(f.filename)
    if not name.lower().endswith(".pdf"): return jsonify({"ok":False,"error":"Envie um PDF."}),400
    in_path=os.path.join(UPLOAD, uuid.uuid4().hex+'_'+name); f.save(in_path)
    tid=make_task()
    def parse_ranges(s, total):
        if not s: return list(range(1,total+1))
        pages=set()
        for part in s.split(","):
            part=part.strip()
            if "-" in part:
                a,b=part.split("-",1); a=int(a); b=int(b)
                for x in range(a,b+1): pages.add(x)
            else:
                pages.add(int(part))
        return [p for p in sorted(pages) if 1<=p<=total]
    def worker():
        try:
            reader=PdfReader(in_path); total=len(reader.pages); want=parse_ranges(ranges,total)
            w=PdfWriter()
            for i,p in enumerate(want,1):
                w.add_page(reader.pages[p-1]); put_progress(tid, progress=int(i/len(want)*100), message=f"Extraindo página {p}...")
            out=os.path.join(OUTPUT, f"extract_{uuid.uuid4().hex}.pdf")
            with open(out,"wb") as fp: w.write(fp)
            put_progress(tid, progress=100, message="Extração concluída.", done=True, download=url_for('download', path=os.path.basename(out)))
        except Exception as e:
            put_progress(tid, error=str(e), done=True)
        finally:
            close_progress(tid); cleanup(in_path)
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok":True,"progress_url":url_for("progress",task_id=tid)})

@app.post("/api/compress")
def api_compress():
    f=request.files.get("file")
    if not f or f.filename=="": return jsonify({"ok":False,"error":"Nenhum arquivo enviado."}),400
    name=secure_filename(f.filename)
    if not name.lower().endswith(".pdf"): return jsonify({"ok":False,"error":"Envie um PDF."}),400
    in_path=os.path.join(UPLOAD, uuid.uuid4().hex+'_'+name); f.save(in_path)
    out=os.path.join(OUTPUT, f"compressed_{uuid.uuid4().hex}.pdf")
    tid=make_task()
    def worker():
        try:
            reader=PdfReader(in_path); w=PdfWriter(); total=len(reader.pages)
            for i in range(total):
                w.add_page(reader.pages[i]); put_progress(tid, progress=int((i+1)/total*100), message=f"Processando página {i+1}/{total}...")
            with open(out,"wb") as fp: w.write(fp)
            put_progress(tid, progress=100, message="Compressão concluída (básica).", done=True, download=url_for('download', path=os.path.basename(out)))
        except Exception as e:
            put_progress(tid, error=str(e), done=True)
        finally:
            close_progress(tid); cleanup(in_path)
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok":True,"progress_url":url_for("progress",task_id=tid)})

@app.get("/progress/<task_id>")
def progress(task_id): return Response(sse_stream(task_id), mimetype="text/event-stream")

@app.get("/download/<path:path>")
def download(path):
    full=os.path.join(OUTPUT, path)
    if not os.path.exists(full): return "Arquivo não encontrado.",404
    return send_file(full, as_attachment=True)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
