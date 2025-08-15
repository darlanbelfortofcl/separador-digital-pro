from pathlib import Path
from typing import List
from PyPDF2 import PdfReader, PdfWriter

def split_pdf_to_folder(src_pdf: Path, out_dir: Path, base_name: str) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(src_pdf))
    written = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = out_dir / f"{base_name}_page_{i}.pdf"
        with open(out_path, "wb") as f_out:
            writer.write(f_out)
        written.append(out_path)
    return written
