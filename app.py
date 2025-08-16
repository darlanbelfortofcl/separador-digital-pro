
import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import zipfile
import io

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Senha fixa definida
ADMIN_PASSWORD = "29031984bB@G"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        senha = request.form.get("password")
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
        return redirect(url_for("login"))

    if "pdf_file" not in request.files:
        flash("Nenhum arquivo enviado", "error")
        return redirect(url_for("index"))

    pdf_file = request.files["pdf_file"]
    if pdf_file.filename == "":
        flash("Nenhum arquivo selecionado", "error")
        return redirect(url_for("index"))

    try:
        filename = secure_filename(pdf_file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        pdf_file.save(filepath)

        reader = PdfReader(filepath)
        option = request.form.get("option")

        if option == "individual":
            mem_zip = io.BytesIO()
            with zipfile.ZipFile(mem_zip, 'w') as zipf:
                for i, page in enumerate(reader.pages, start=1):
                    writer = PdfWriter()
                    writer.add_page(page)
                    output_stream = io.BytesIO()
                    writer.write(output_stream)
                    output_stream.seek(0)
                    zipf.writestr(f"pagina_{i}.pdf", output_stream.read())
            mem_zip.seek(0)
            return send_file(mem_zip, as_attachment=True, download_name="pdf_dividido.zip")

        elif option == "intervalo":
            inicio = int(request.form.get("inicio"))
            fim = int(request.form.get("fim"))
            if inicio < 1 or fim > len(reader.pages) or inicio > fim:
                flash("Intervalo inválido", "error")
                return redirect(url_for("index"))

            writer = PdfWriter()
            for i in range(inicio-1, fim):
                writer.add_page(reader.pages[i])

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            return send_file(output, as_attachment=True, download_name="pdf_intervalo.pdf")

        else:
            flash("Opção inválida", "error")
            return redirect(url_for("index"))

    except Exception as e:
        flash(f"Erro ao dividir PDF: {str(e)}", "error")
        return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
