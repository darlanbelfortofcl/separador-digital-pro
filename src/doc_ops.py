from pathlib import Path
from docx import Document
from pdfminer.high_level import extract_text

def pdf_to_docx(src: Path, out_docx: Path) -> Path:
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    text = extract_text(str(src)) or ""
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(str(out_docx))
    return out_docx
