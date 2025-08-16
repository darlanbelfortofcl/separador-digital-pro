from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.secret_key = "segredo"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'file' not in request.files:
            flash("Nenhum arquivo enviado", "erro")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("Nenhum arquivo selecionado", "erro")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Divisão do PDF
            reader = PdfReader(filepath)
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"pagina_{i+1}.pdf")
                with open(output_path, "wb") as output_pdf:
                    writer.write(output_pdf)

            flash("PDF dividido com sucesso!", "sucesso")
            return redirect(url_for('download'))
        else:
            flash("Envie um arquivo PDF válido", "erro")
            return redirect(request.url)
    return render_template("index.html")

@app.route("/download")
def download():
    files = os.listdir(app.config['OUTPUT_FOLDER'])
    return render_template("download.html", files=files)

@app.route("/baixar/<nome>")
def baixar(nome):
    path = os.path.join(app.config['OUTPUT_FOLDER'], nome)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
