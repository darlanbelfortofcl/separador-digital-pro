
import os
from typing import Optional, Callable
from PyPDF2 import PdfReader, PdfWriter

def processar_pdf(caminho_pdf: str, pasta_destino: str, pasta_otimizada: str,
                  qualidade: str="ebook", timeout: int=60, limpar: bool=False, threads: int=4,
                  callback: Optional[Callable]=None):
    """
    Divide PDF em páginas individuais. (Otimização/qualidade simulada)
    """
    reader = PdfReader(caminho_pdf)
    total = len(reader.pages)
    if total == 0:
        raise RuntimeError("PDF sem páginas.")

    os.makedirs(pasta_destino, exist_ok=True)
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = os.path.join(pasta_destino, f"pagina_{i:03d}.pdf")
        with open(out_path, "wb") as f:
            writer.write(f)
        if callback:
            callback("Dividindo", i, total)
