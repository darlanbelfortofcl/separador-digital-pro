
# Separador Digital Pro — versão rápida (SSE + PyMuPDF)

Conversão **mais rápida** e estável:
- **PDF → DOCX** usando **PyMuPDF** com render em paralelo (Rápido/Equilibrado/Alta)
- **DOCX → PDF** via `docx2pdf` (Windows/Mac; no Linux requer LibreOffice)
- **Dividir PDF** com progresso
- **SSE com keep-alive** (evita quedas no Render)
- UI moderna, responsiva e com rastro de mouse

## Como rodar
```bash
pip install -r requirements.txt
python app.py
# http://localhost:5000
```

## Deploy Render
Build: `pip install -r requirements.txt`  
Start: `gunicorn app:app`

## Observações
- Em Linux/Render, a conversão **DOCX→PDF** pode não funcionar sem instalar LibreOffice ou similar.
- A conversão **PDF→DOCX** é fiel (cada página como imagem no DOCX) e **muito mais rápida**.
