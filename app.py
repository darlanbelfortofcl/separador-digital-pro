
from flask import Flask, request, jsonify, render_template, send_file
import os
from PyPDF2 import PdfReader, PdfWriter

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/split", methods=["POST"])
def split_pdfs():
    if "files" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    files = request.files.getlist("files")
    response_files = []

    for file in files:
        if not file or file.filename == "" or not file.filename.lower().endswith(".pdf"):
            continue

        # Salva temporariamente para leitura pelo PyPDF2
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)

        try:
            reader = PdfReader(input_path)

            # Se estiver criptografado e não destravar, pula o arquivo
            if getattr(reader, "is_encrypted", False):
                try:
                    ok = reader.decrypt("")
                    if ok == 0:
                        response_files.append({"name": file.filename, "url": "", "error": "PDF protegido por senha"})
                        continue
                except Exception:
                    response_files.append({"name": file.filename, "url": "", "error": "PDF protegido por senha"})
                    continue

            for i, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)

                # Mantém o nome original
                base_name = os.path.splitext(os.path.basename(file.filename))[0]
                output_filename = f"{base_name}_pagina_{i}.pdf"
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                with open(output_path, "wb") as f_out:
                    writer.write(f_out)

                response_files.append({
                    "name": output_filename,
                    "url": f"/download/{output_filename}"
                })

        except Exception as e:
            response_files.append({"name": file.filename, "url": "", "error": f"Falha ao processar: {e}"})
        finally:
            # Opcional: remover o upload para economizar espaço
            try:
                os.remove(input_path)
            except Exception:
                pass

    if not response_files:
        return jsonify({"error": "Nenhum PDF válido foi enviado."}), 400

    return jsonify({"files": response_files})

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    # Para rodar local: python app.py
    app.run(host="0.0.0.0", port=5000, debug=True)
