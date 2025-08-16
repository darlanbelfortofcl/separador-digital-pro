from pathlib import Path
from typing import Optional, Callable

from PyPDF2 import PdfReader, PdfWriter

Callback = Optional[Callable[[str, int, int], None]]


def split_pdf(pdf_path: Path, out_dir: Path, optimized_dir: Path,
              limpar: bool = False, callback: Callback = None) -> None:
    name = pdf_path.name
    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)

    out_dir.mkdir(parents=True, exist_ok=True)
    optimized_dir.mkdir(parents=True, exist_ok=True)

    if total == 0:
        if callback:
            callback(name, 0, 0)
        return

    # Loop simples (PyPDF2 não paraleliza páginas de forma segura por padrão)
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        page_path = out_dir / f"{pdf_path.stem}_pag_{i}.pdf"
        with open(page_path, "wb") as f:
            writer.write(f)

        # "Otimização" placeholder: duplicar arquivo para a pasta de otimizados
        opt_path = optimized_dir / f"{pdf_path.stem}_pag_{i}_otimizado.pdf"
        try:
            with open(page_path, "rb") as src, open(opt_path, "wb") as dst:
                dst.write(src.read())
        except Exception:
            # Se falhar a cópia, segue o processamento
            pass

        if callback:
            callback(name, i, total)

    if limpar:
        try:
            pdf_path.unlink(missing_ok=True)
        except Exception:
            pass
