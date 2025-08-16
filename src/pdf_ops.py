from pathlib import Path
from typing import List
from PyPDF2 import PdfReader, PdfWriter

def validate_pdf(path: Path) -> None:
    # Try opening the document to ensure it's readable & not encrypted
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise ValueError("PDF protegido por senha não é suportado.")
    # Access first page to trigger parse
    _ = reader.pages[0] if len(reader.pages) else None

def split_pdf(src: Path, out_dir: Path) -> List[Path]:
    validate_pdf(src)
    reader = PdfReader(str(src))
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = out_dir / f"{src.stem}_p{i:03d}.pdf"
        with open(out_path, "wb") as f:
            writer.write(f)
        outputs.append(out_path)
    return outputs

def merge_pdfs(src_files: List[Path], out_path: Path) -> Path:
    writer = PdfWriter()
    for f in src_files:
        validate_pdf(f)
        r = PdfReader(str(f))
        for p in r.pages:
            writer.add_page(p)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as fp:
        writer.write(fp)
    return out_path
