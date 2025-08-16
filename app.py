
import os
import io
import zipfile
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, jsonify
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_PASSWORD = "29031984bB@G"

def parse_intervalos(intervalos_str, total_pages):
    results = []
    s = (intervalos_str or "").replace(" ", "")
    if not s:
        return results
    for part in s.split(","):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                ini = max(1, int(a))
                fim = min(total_pages, int(b))
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

def dividir_todas(reader):
    outputs = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        outputs.append((f"pagina_{i}.pdf", buf))
    return outputs

def dividir_intervalos(reader, intervalos_str):
    ranges = parse_intervalos(intervalos_str, len(reader.pages))
    outputs = []
    for idx, (ini, fim) in enumerate(ranges, start=1):
        writer = PdfWriter()
        for i in range(ini, fim + 1):
            writer.add_page(reader.pages[i])
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        outputs.append((f"intervalo_{idx}_{ini+1}-{fim+1}.pdf", buf))
    return outputs

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password", "") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
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
    modo = request.form.get("modo")
    intervalos = request.form.get("intervalos", "")

    if not files:
        return jsonify({"ok": False, "msg": "Nenhum arquivo selecionado."}), 400
    if modo not in ("todas", "intervalos"):
        return jsonify({"ok": False, "msg": "Modo inválido."}), 400
    if modo == "intervalos" and not intervalos.strip():
        return jsonify({"ok": False, "msg": "Informe intervalos no formato 1-3,5,7-9."}), 400

    total_arquivos = 0
    total_saidas = 0
    relatorio = []

    zip_mem = io.BytesIO()
    with zipfile.ZipFile(zip_mem, "w", compression=zipfile.ZIP_DEFLATED) as zipf:

        for fs in files:
            if not fs or not fs.filename.lower().endswith(".pdf"):
                continue

            total_arquivos += 1
            nome = secure_filename(fs.filename)
            pasta = os.path.splitext(nome)[0]

            try:
                # Ler de forma robusta (lida com streams não seekable)
                data = fs.read()
                if not data:
                    relatorio.append(f"[ERRO] {nome}: arquivo vazio.")
                    continue
                buf = io.BytesIO(data)

                try:
                    reader = PdfReader(buf)
                except Exception as e:
                    relatorio.append(f"[ERRO] {nome}: não foi possível abrir como PDF ({e}).")
                    continue

                # Descriptografar se necessário
                if getattr(reader, "is_encrypted", False):
                    try:
                        if not reader.decrypt(""):  # tenta sem senha
                            relatorio.append(f"[ERRO] {nome}: PDF protegido por senha.")
                            continue
                    except Exception:
                        relatorio.append(f"[ERRO] {nome}: PDF protegido por senha.")
                        continue

                if len(reader.pages) == 0:
                    relatorio.append(f"[ERRO] {nome}: sem páginas legíveis.")
                    continue

                if modo == "todas":
                    partes = dividir_todas(reader)
                else:
                    partes = dividir_intervalos(reader, intervalos)
                    if not partes:
                        relatorio.append(f"[ERRO] {nome}: nenhum intervalo válido (ex.: 1-3,5).")
                        continue

                for saida_nome, saida_buf in partes:
                    zipf.writestr(f"{pasta}/{saida_nome}", saida_buf.getvalue())
                    total_saidas += 1

                relatorio.append(f"[OK] {nome}: {len(partes)} arquivo(s) gerado(s).")

            except Exception as e:
                relatorio.append(f"[ERRO] {nome}: falha inesperada ({e}).")
                continue

        # Anexa um relatório no zip
        rel = "\n".join([
            "Relatório de processamento — Separador Digital Pro",
            f"Arquivos enviados: {total_arquivos}",
            f"Arquivos gerados: {total_saidas}",
            "-"*50,
            *relatorio
        ])
        zipf.writestr("relatorio.txt", rel)

    if total_saidas == 0:
        # Nenhum arquivo produzido, retorna erro + detalhes do relatório
        return jsonify({"ok": False, "msg": "Nenhum PDF pôde ser processado. Verifique os intervalos e se os arquivos não estão protegidos por senha."}), 400

    zip_mem.seek(0)
    return send_file(zip_mem, as_attachment=True, download_name="pdfs_divididos.zip")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
