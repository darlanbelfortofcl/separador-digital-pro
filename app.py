
import os
import io
import zipfile
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, jsonify
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter

app = Flask(__name__)
app.secret_key = "supersecretkey"  # para sessão e flash

# Senha fixa (a pedido)
ADMIN_PASSWORD = "29031984bB@G"

def parse_intervalos(intervalos_str, total_pages):
    # Converte '1-3,5,7-9' para lista de ranges (0-based, inclusivo)
    results = []
    s = (intervalos_str or "").replace(" ", "")
    if not s:
        return results
    for part in s.split(","):
        if not part:
            continue
        if "-" in part:
            ini_s, fim_s = part.split("-", 1)
            try:
                ini = max(1, int(ini_s))
                fim = min(total_pages, int(fim_s))
            except:
                continue
            if ini <= fim:
                results.append((ini-1, fim-1))
        else:
            try:
                p = int(part)
            except:
                continue
            if 1 <= p <= total_pages:
                results.append((p-1, p-1))
    return results

def dividir_pdf_em_paginas(reader):
    outputs = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        outputs.append((f"pagina_{i}.pdf", buf))
    return outputs

def dividir_pdf_por_intervalos(reader, intervalos_str):
    ranges = parse_intervalos(intervalos_str, len(reader.pages))
    outputs = []
    if not ranges:
        return outputs
    for idx, (ini, fim) in enumerate(ranges, start=1):
        writer = PdfWriter()
        for i in range(ini, fim+1):
            writer.add_page(reader.pages[i])
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        outputs.append((f"intervalo_{idx}_{ini+1}-{fim+1}.pdf", buf))
    return outputs

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        senha = request.form.get("password", "")
        if senha == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            flash("Senha incorreta!", "error")
    return render_template("login.html")

@app.route("/index")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/dividir", methods=["POST"])
def dividir():
    if not session.get("logged_in"):
        return jsonify({"ok": False, "msg": "Não autorizado."}), 401

    files = request.files.getlist("pdf_files")
    modo = request.form.get("modo")  # 'todas' ou 'intervalos'
    intervalos = request.form.get("intervalos", "")

    if not files:
        return jsonify({"ok": False, "msg": "Nenhum arquivo enviado."}), 400
    if modo not in ("todas", "intervalos"):
        return jsonify({"ok": False, "msg": "Modo inválido."}), 400

    try:
        zip_mem = io.BytesIO()
        with zipfile.ZipFile(zip_mem, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for f in files:
                if not f or not f.filename.lower().endswith(".pdf"):
                    continue
                filename = secure_filename(f.filename)
                stem = os.path.splitext(filename)[0]
                reader = PdfReader(f.stream)

                if modo == "todas":
                    parts = dividir_pdf_em_paginas(reader)
                else:
                    parts = dividir_pdf_por_intervalos(reader, intervalos)
                    if not parts:
                        # se intervalos inválidos, pula arquivo
                        continue

                # Organiza por subpasta com nome do arquivo original
                for name, buf in parts:
                    zipf.writestr(f"{stem}/{name}", buf.getvalue())

        zip_mem.seek(0)
        # Para XHR com responseType=blob, retornamos diretamente o arquivo
        return send_file(zip_mem, as_attachment=True, download_name="pdfs_divididos.zip")

    except Exception as e:
        return jsonify({"ok": False, "msg": f"Erro ao processar: {str(e)}"}), 500

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
