
import os
import platform
import subprocess

def convert_pdf_to_docx(src_path, dst_path):
    from pdf2docx import Converter
    cv = Converter(src_path)
    try:
        cv.convert(dst_path, start=0, end=None)
    finally:
        cv.close()

def _has_libreoffice():
    for cmd in ("soffice", "libreoffice"):
        try:
            subprocess.run([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            return True
        except FileNotFoundError:
            continue
    return False

def convert_docx_to_pdf(src_path, dst_path):
    if platform.system().lower().startswith("win"):
        from docx2pdf import convert
        convert(src_path, dst_path)
        return

    if _has_libreoffice():
        out_dir = os.path.dirname(dst_path)
        os.makedirs(out_dir, exist_ok=True)
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", out_dir, src_path], check=True)
        base = os.path.splitext(os.path.basename(src_path))[0] + ".pdf"
        gen = os.path.join(out_dir, base)
        if gen != dst_path:
            try:
                os.replace(gen, dst_path)
            except Exception:
                pass
        return

    raise RuntimeError("Conversão DOCX→PDF requer Windows (docx2pdf) ou LibreOffice instalado no servidor.")
