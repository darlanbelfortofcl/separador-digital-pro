
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable, List, Tuple

# PDF -> DOCX rápido e fiel via render de páginas (PyMuPDF) + python-docx
import fitz  # PyMuPDF
from docx import Document
from docx.shared import Inches
from docx.enum.section import WD_ORIENT

# DOCX -> PDF quando disponível
def _has_docx2pdf():
    try:
        import docx2pdf  # type: ignore
        return True
    except Exception:
        return False

def convert_docx_to_pdf(src_path: str, out_path: str, callback: Optional[Callable]=None):
    """
    Usa docx2pdf se estiver disponível (Windows/Mac).
    Em ambientes Linux (Render), essa função pode não funcionar sem LibreOffice.
    """
    if callback: callback("Preparando", 0, 100)
    if not _has_docx2pdf():
        raise RuntimeError("Conversão DOCX→PDF requer docx2pdf (Windows/Mac) ou LibreOffice no servidor.")
    from docx2pdf import convert  # type: ignore
    convert(src_path, out_path)
    if callback: callback("Finalizando", 100, 100)

def _render_page(args) -> Tuple[int, bytes]:
    idx, pdf_path, dpi = args
    doc = fitz.open(pdf_path)
    page = doc.load_page(idx)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_bytes = pix.tobytes("png")
    doc.close()
    return idx, img_bytes

def convert_pdf_to_docx(src_path: str, out_path: str, qualidade: str="equilibrado", workers: int=4, callback: Optional[Callable]=None):
    """
    Converte um PDF em DOCX renderizando cada página como imagem.
    Modos:
      - rapido:      DPI ~110 (mais veloz, menor arquivo)
      - equilibrado: DPI ~150 (recomendado)
      - alta:        DPI ~200 (qualidade melhor, mais lento)
    """
    dpi_map = {"rapido": 110, "equilibrado": 150, "alta": 200}
    dpi = dpi_map.get(qualidade, 150)

    doc_pdf = fitz.open(src_path)
    total = doc_pdf.page_count
    doc_pdf.close()

    if total == 0:
        raise RuntimeError("PDF sem páginas.")

    # Renderiza páginas em paralelo
    if callback: callback("Renderizando páginas…", 1, 100)
    tasks = [(i, src_path, dpi) for i in range(total)]
    results: List[Tuple[int, bytes]] = [None]*total  # type: ignore

    done_pages = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        fut_map = {ex.submit(_render_page, t): t[0] for t in tasks}
        for fut in as_completed(fut_map):
            idx, img = fut.result()
            results[idx] = (idx, img)
            done_pages += 1
            if callback:
                # progresso 5%..85%
                pct = 5 + int((done_pages/total)*80)
                callback(f"Página {done_pages}/{total} renderizada", pct, 100)

    # Monta DOCX preservando tamanho em A4
    if callback: callback("Gerando DOCX…", 90, 100)
    document = Document()
    # Ajusta seção para A4 retrato
    section = document.sections[0]
    section.page_width, section.page_height = (Inches(8.27), Inches(11.69))

    for idx, img_bytes in results:
        if idx != 0:
            document.add_page_break()
        # Salva temporariamente a imagem
        tmp_img = f"{out_path}.p{idx}.png"
        with open(tmp_img, "wb") as f:
            f.write(img_bytes)
        # Inserir imagem com largura da página (margens padrão ~1")
        document.add_picture(tmp_img, width=Inches(6.5))
        os.remove(tmp_img)

    document.save(out_path)
    if callback: callback("Concluído", 100, 100)
