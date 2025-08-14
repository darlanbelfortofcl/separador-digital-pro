
from pdf2docx import Converter
import platform

def convert_pdf_to_docx(src_pdf: str, out_docx: str):
    """
    Converte PDF -> DOCX (EDITÁVEL) usando pdf2docx.
    """
    cv = Converter(src_pdf)
    try:
        cv.convert(out_docx, start=0, end=None)
    finally:
        cv.close()

def convert_docx_to_pdf(src_docx: str, out_pdf: str):
    """
    Converte DOCX -> PDF. Em Windows/Mac usa docx2pdf (Word).
    Em Linux/Render, requer LibreOffice; se não disponível, levanta erro claro.
    """
    try:
        import docx2pdf  # type: ignore
    except Exception:
        raise RuntimeError("DOCX→PDF requer 'docx2pdf' (Windows/Mac) ou LibreOffice no Linux.")

    try:
        from docx2pdf import convert as d2p_convert
        d2p_convert(src_docx, out_pdf)
    except Exception as e:
        raise RuntimeError(f"Falha ao converter DOCX→PDF: {e}")
