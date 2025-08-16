from io import BytesIO
from typing import Callable, Optional, List, Tuple
from PyPDF2 import PdfReader, PdfWriter

def parse_ranges(ranges: str, total_pages: int) -> List[int]:
    pages = set()
    for part in (ranges or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                start = int(a); end = int(b)
            except ValueError:
                continue
            if start > end:
                start, end = end, start
            for p in range(start, end + 1):
                if 1 <= p <= total_pages:
                    pages.add(p)
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.add(p)
            except ValueError:
                continue
    if not pages:
        return list(range(1, total_pages + 1))
    return sorted(pages)

def split_pdf_to_disk(input_path: str, out_dir: str, pages: List[int]) -> List[Tuple[int, str]]:
    """
    Divide o PDF e salva cada página como um arquivo PDF individual.
    Retorna lista de (page_number, file_path).
    """
    import os
    os.makedirs(out_dir, exist_ok=True)
    reader = PdfReader(input_path)
    saved = []
    pad = len(str(len(pages)))
    for page_number in pages:
        writer = PdfWriter()
        writer.add_page(reader.pages[page_number - 1])
        file_path = os.path.join(out_dir, f"pagina_{str(page_number).zfill(pad)}.pdf")
        with open(file_path, "wb") as f:
            writer.write(f)
        saved.append((page_number, file_path))
    return saved

def zip_paths(file_paths: List[str], zip_path: str) -> str:
    import zipfile, os
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            zf.write(fp, arcname=os.path.basename(fp))
    return zip_path
