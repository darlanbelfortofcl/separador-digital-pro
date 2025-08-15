from pathlib import Path
from PyPDF2 import PdfWriter
from src.utils import validate_pdf
def test_valid_pdf(tmp_path: Path):
    pdf_path=tmp_path / 'sample.pdf'
    w=PdfWriter(); w.add_blank_page(width=72, height=72)
    with open(pdf_path,'wb') as f: w.write(f)
    meta=validate_pdf(pdf_path)
    assert meta['pages']==1
