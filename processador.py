import os, shutil, subprocess, math
from typing import Callable, List, Optional
from PyPDF2 import PdfReader, PdfWriter

# ---------- Divisão ----------
def split_pdf_all(src_pdf: str, out_dir: str, callback: Optional[Callable[[int,int],None]] = None):
    reader = PdfReader(src_pdf)
    total = len(reader.pages)
    os.makedirs(out_dir, exist_ok=True)
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        out = os.path.join(out_dir, f"page_{i}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        if callback: callback(i, total)

def _parse_ranges(ranges: str, total: int) -> List[int]:
    # Ex: "1-3,5,8-10"
    pages = set()
    for token in ranges.replace(" ", "").split(","):
        if not token: 
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            a = int(a); b = int(b)
            for p in range(max(1,a), min(total,b)+1):
                pages.add(p)
        else:
            pages.add(int(token))
    return sorted([p for p in pages if 1 <= p <= total])

def split_pdf_by_ranges(src_pdf: str, out_dir: str, ranges: str, callback: Optional[Callable[[int,int],None]] = None):
    reader = PdfReader(src_pdf)
    total = len(reader.pages)
    os.makedirs(out_dir, exist_ok=True)
    selected = _parse_ranges(ranges, total)
    count = 0
    for i in selected:
        writer = PdfWriter()
        writer.add_page(reader.pages[i-1])
        out = os.path.join(out_dir, f"page_{i}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        count += 1
        if callback: callback(count, len(selected))

def split_pdf_by_pages(src_pdf: str, out_dir: str, pages: str, callback: Optional[Callable[[int,int],None]] = None):
    # pages é uma lista separada por vírgula: "2,5,7"
    return split_pdf_by_ranges(src_pdf, out_dir, pages, callback)

# ---------- Compressão ----------
def _has_cmd(cmd: str) -> bool:
    try:
        subprocess.run([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False

def _ghostscript_compress(src_pdf: str, dst_pdf: str, quality: str = "medium"):
    # quality: 'low','medium','high'
    preset = {
        "low": "/screen",
        "medium": "/ebook",
        "high": "/printer"
    }.get(quality, "/ebook")
    args = [
        "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={preset}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={dst_pdf}", src_pdf
    ]
    subprocess.run(args, check=True)

def _pymupdf_compress(src_pdf: str, dst_pdf: str, quality: str = "medium", progress=None):
    import fitz  # PyMuPDF
    zoom = {"low": 0.6, "medium": 0.8, "high": 1.0}.get(quality, 0.8)
    doc = fitz.open(src_pdf)
    total = len(doc)
    for i in range(total):
        page = doc[i]
        # Simplified: downscale images via re-creating page as pixmap and re-inserting
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        rect = page.rect
        new_pdf = fitz.open()
        new_page = new_pdf.new_page(width=rect.width, height=rect.height)
        img = new_pdf.new_page()  # workaround placeholder to get xref for image
        new_pdf.delete_page(-1)
        img_xref = new_pdf.insert_image(rect, pixmap=pix)
        # Not a perfect technique; alternative is to rasterize full page
        # We'll rasterize page to image then build a single-image page
        new_pdf.close()
        # Fallback full document rasterization to maintain layout
        # (We create image per page and append to out_doc)
        if i == 0:
            out_doc = fitz.open()
        img_page = out_doc.new_page(width=rect.width, height=rect.height)
        img_page.insert_image(rect, pixmap=pix)
        if progress:
            progress(int((i+1)/total*95))
    out_doc.save(dst_pdf)
    out_doc.close()
    if progress:
        progress(98)

def compress_pdf(src_pdf: str, dst_pdf: str, quality: str = "medium", progress=None):
    os.makedirs(os.path.dirname(dst_pdf), exist_ok=True)
    if _has_cmd("gs"):
        _ghostscript_compress(src_pdf, dst_pdf, quality=quality)
        if progress: progress(100)
        return
    # Fallback: PyMuPDF rasterization approach
    _pymupdf_compress(src_pdf, dst_pdf, quality=quality, progress=progress)
    if progress: progress(100)
