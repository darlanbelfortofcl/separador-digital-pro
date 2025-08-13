import os
import subprocess
import shutil
import logging
from PyPDF2 import PdfReader, PdfWriter
from concurrent.futures import ThreadPoolExecutor

def encontrar_ghostscript():
    possiveis = [
        r"C:\Program Files\gs\gs10.02.0\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs9.56.1\bin\gswin64c.exe",
        r"C:\Program Files (x86)\gs\gs10.02.0\bin\gswin32c.exe",
        shutil.which("gswin64c"),
        shutil.which("gs")
    ]
    for caminho in possiveis:
        if caminho and os.path.exists(caminho):
            return caminho
    return None

def otimizar_pdf(gs_path, entrada, saida, qualidade, timeout):
    try:
        subprocess.run(
            [
                gs_path, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS=/{qualidade}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
                f"-sOutputFile={saida}", entrada
            ],
            check=True,
            timeout=timeout,
            capture_output=True
        )
        return True
    except subprocess.TimeoutExpired:
        logging.warning(f"Otimização de '{entrada}' demorou demais e foi pulada.")
    except Exception as e:
        logging.error(f"Erro ao otimizar '{entrada}': {e}")
    return False

def processar_pagina(pagina, indice, nome_base, pasta_destino, pasta_otimizada, gs_path, qualidade, timeout, limpar, callback):
    escritor = PdfWriter()
    escritor.add_page(pagina)

    nome_saida = f"{nome_base}_pagina_{indice + 1}.pdf"
    caminho_saida = os.path.join(pasta_destino, nome_saida)

    with open(caminho_saida, "wb") as saida_pdf:
        escritor.write(saida_pdf)

    if gs_path:
        caminho_otimizado = os.path.join(pasta_otimizada, nome_saida)
        sucesso = otimizar_pdf(gs_path, caminho_saida, caminho_otimizado, qualidade, timeout)
        if sucesso and limpar:
            os.remove(caminho_saida)

    if callback:
        callback(indice + 1)

def processar_pdf(caminho_pdf, pasta_destino, pasta_otimizada, qualidade="ebook", timeout=60, limpar=False, threads=4, callback=None):
    gs_path = encontrar_ghostscript()
    nome_arquivo = os.path.basename(caminho_pdf)
    nome_base = os.path.splitext(nome_arquivo)[0]

    try:
        leitor = PdfReader(caminho_pdf)
        total_paginas = len(leitor.pages)
        logging.info(f"Processando '{nome_arquivo}' com {total_paginas} páginas.")

        progresso = {"atual": 0}

        def cb(pagina_atual):
            progresso["atual"] = pagina_atual
            if callback:
                callback(nome_arquivo, pagina_atual, total_paginas)

        with ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(lambda args: processar_pagina(*args),
                [(pagina, i, nome_base, pasta_destino, pasta_otimizada, gs_path, qualidade, timeout, limpar, cb)
                 for i, pagina in enumerate(leitor.pages)]
            )

        return f"✅ '{nome_arquivo}' dividido em {total_paginas} páginas."

    except Exception as e:
        logging.error(f"Erro ao abrir '{nome_arquivo}': {e}")
        return f"❌ Erro ao processar '{nome_arquivo}'."
