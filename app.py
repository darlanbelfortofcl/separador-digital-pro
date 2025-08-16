from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
from PyPDF2 import PdfReader, PdfWriter
import zipfile
import uuid

app = Flask(__name__)
app.secret_key = "29031984bB@G"

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/divide", methods=["POST"])
def divide():
    if "pdfs" not in request.files:
        flash("Nenhum arquivo enviado!", "error")
        return redirect(url_for("index"))

    pdf_files = request.files.getlist("pdfs")
    pages = request.form.get("pages")

    if not pages:
        flash("Informe as páginas para dividir!", "error")
        return redirect(url_for("index"))

    pages = [int(p.strip()) - 1 for p in pages.split(",") if p.strip().isdigit()]

    zip_filename = os.path.join(OUTPUT_FOLDER, f"divididos_{uuid.uuid4().hex}.zip")
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for pdf_file in pdf_files:
            if pdf_file.filename == "":
                continue

            input_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
            pdf_file.save(input_path)

            try:
                reader = PdfReader(input_path)
                for i, page_num in enumerate(pages, start=1):
                    if 0 <= page_num < len(reader.pages):
                        writer = PdfWriter()
                        writer.add_page(reader.pages[page_num])

                        output_pdf_name = f"{os.path.splitext(pdf_file.filename)[0]}_pagina_{page_num+1}.pdf"
                        output_path = os.path.join(OUTPUT_FOLDER, output_pdf_name)

                        with open(output_path, "wb") as f_out:
                            writer.write(f_out)

                        zipf.write(output_path, arcname=output_pdf_name)
            except Exception as e:
                flash(f"Erro ao processar {pdf_file.filename}: {str(e)}", "error")
                return redirect(url_for("index"))

    return send_file(zip_filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
