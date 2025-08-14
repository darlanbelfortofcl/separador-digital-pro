
import os
from PyPDF2 import PdfReader, PdfWriter

def processar_pdf(caminho_pdf, pasta_destino, pasta_otimizada, qualidade="ebook", timeout=60, limpar=False, threads=4, callback=None):
    nome = os.path.basename(caminho_pdf)
    reader = PdfReader(caminho_pdf)
    total = len(reader.pages)
    if total == 0:
        if callback: callback(nome, 0, 0)
        return

    os.makedirs(pasta_destino, exist_ok=True)
    os.makedirs(pasta_otimizada, exist_ok=True)

    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        saida_pagina = os.path.join(pasta_destino, f"{os.path.splitext(nome)[0]}_pag_{i}.pdf")
        with open(saida_pagina, "wb") as f:
            writer.write(f)

        # Simulação de otimização: copia para a pasta "otimizados"
        otimizado = os.path.join(pasta_otimizada, f"{os.path.splitext(nome)[0]}_pag_{i}_otimizado.pdf")
        try:
            with open(saida_pagina, "rb") as src, open(otimizado, "wb") as dst:
                dst.write(src.read())
        except Exception:
            pass

        if callback:
            callback(nome, i, total)

    if limpar:
        try:
            os.remove(caminho_pdf)
        except Exception:
            pass
