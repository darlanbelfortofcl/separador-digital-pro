
import os, platform
from typing import Callable, Optional
from pdf2docx import Converter
from PyPDF2 import PdfReader

def _count_pages(pdf_path:str)->int:
    try:
        with open(pdf_path, "rb") as f:
            r = PdfReader(f)
            return len(r.pages)
    except Exception:
        return 0

def convert_pdf_to_docx(src_pdf:str, out_docx:str, turbo:bool=True, callback: Optional[Callable[[int, str], None]] = None):
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
            pct = int(p * 98)  # p: 0..1
            callback(min(98, max(2, pct)), "Convertendo…")

    with Converter(src_pdf) as cv:
        cv.convert(out_docx, start=0, end=None, layout_mode=layout_mode, progress=_progress)

    if callback:
        callback(100, "Conversão finalizada.")

def convert_docx_to_pdf(src_docx:str, out_pdf:str):
    try:
        from docx2pdf import convert as d2p_convert
    except Exception as e:
        raise RuntimeError("Conversão DOCX→PDF requer docx2pdf (Word/Office instalado).") from e

    d2p_convert(src_docx, out_pdf)
