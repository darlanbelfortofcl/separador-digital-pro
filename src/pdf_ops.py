from pathlib import Path
from typing import List
from PyPDF2 import PdfReader, PdfWriter
def split_pdf(src:Path, out_dir:Path, base_name:str)->list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    reader=PdfReader(str(src)); written=[]
    for i,page in enumerate(reader.pages, start=1):
        writer=PdfWriter(); writer.add_page(page)
        out_path=out_dir / f"{base_name}_page_{i}.pdf"
        with open(out_path,'wb') as f: writer.write(f)
        written.append(out_path)
    return written
def merge_pdfs(paths:list[Path], out_path:Path)->Path:
    writer=PdfWriter()
    for p in paths:
        reader=PdfReader(str(p))
        for page in reader.pages: writer.add_page(page)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path,'wb') as f: writer.write(f)
    return out_path
def compress_pdf(src:Path, out_path:Path)->Path:
    reader=PdfReader(str(src)); writer=PdfWriter()
    for page in reader.pages: writer.add_page(page)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path,'wb') as f: writer.write(f)
    return out_path
