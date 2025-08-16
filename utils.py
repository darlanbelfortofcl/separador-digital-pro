from io import BytesIO
from typing import Callable, Optional, List
from PyPDF2 import PdfReader, PdfWriter

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_ranges(ranges: str, total_pages: int) -> List[int]:
    pages = set()
    for part in ranges.split(","):
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
    return sorted(pages)

def split_pdf_with_progress(input_path: str, output_zip_path: str, progress_callback: Callable[[int,str],None], ranges: Optional[str]=None) -> None:
    import os, zipfile
    reader = PdfReader(input_path)
    total = len(reader.pages)
    if ranges:
        pages_list = parse_ranges(ranges, total_pages=total) or list(range(1,total+1))
    else:
        pages_list = list(range(1,total+1))

    os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)
    processed = 0
    pad = len(str(len(pages_list)))

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for page_number in pages_list:
            writer = PdfWriter()
            writer.add_page(reader.pages[page_number-1])
            mem = BytesIO()
            writer.write(mem)
            mem.seek(0)
            zf.writestr(f"pagina_{str(page_number).zfill(pad)}.pdf", mem.read())
            processed += 1
            progress = int(processed*100/len(pages_list))
            progress_callback(progress, f"Processando página {processed}/{len(pages_list)}")
    progress_callback(100, "Concluído")
