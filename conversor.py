import platform
from typing import Callable, Optional
from pathlib import Path

from pdf2docx import Converter
from PyPDF2 import PdfReader


def _count_pages(pdf_path: Path) -> int:
    try:
        with open(pdf_path, "rb") as f:
            r = PdfReader(f)
            return len(r.pages)
    except Exception:
        return 0


def convert_pdf_to_docx(src_pdf: Path, out_docx: Path, turbo: bool = True,
                         callback: Optional[Callable[[int, str], None]] = None):
    """
    Converte PDF -> DOCX editável usando pdf2docx.
    turbo=True usa layout_mode='loose' (mais rápido).

    callback(pct:int, msg:str|None) para progresso.
    """
    pages = _count_pages(src_pdf)
    if callback:
        callback(2, "Lendo documento…")

    layout_mode = "loose" if turbo else "exact"

    def _progress(p):
        if callback:
            pct = int(2 + p * 96)  # 2..98
            callback(min(98, max(2, pct)), f"Convertendo… ({pages} páginas)")

    cv = Converter(str(src_pdf))
    cv.convert(str(out_docx), start=0, end=None, layout_mode=layout_mode, progress=_progress)
    cv.close()

    if callback:
        callback(100, "Conversão finalizada.")


def convert_docx_to_pdf(src_docx: Path, out_pdf: Path):
    # docx2pdf requer Office instalado (Windows/macOS). Em Linux, costuma falhar.
    system = platform.system().lower()
    if system not in {"windows", "darwin"}:
        raise RuntimeError("DOCX→PDF indisponível: requer Word/Office (Windows/macOS).")

    try:
        from docx2pdf import convert as d2p_convert
    except Exception as e:
        raise RuntimeError("Conversão DOCX→PDF requer docx2pdf (Word/Office instalado).") from e

    d2p_convert(str(src_docx), str(out_pdf))
