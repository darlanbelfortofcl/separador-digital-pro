# PDF Toolkit (editável)

Ferramenta Flask para **converter PDF → DOCX editável**, dividir e mesclar PDFs. Compatível com **Render** (Procfile) e pronta para GitHub.

## Funcionalidades
- PDF → **DOCX editável** (texto) usando `pdfminer.six` + `python-docx`.
- **Dividir** PDFs em páginas individuais (gera ZIP).
- **Mesclar** vários PDFs em um único arquivo.
- Dark/Light mode persistente.

## Executar localmente
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_DEBUG=1
python -m src.app
# ou
gunicorn src.app:app -b 0.0.0.0:5000
```

## Deploy no Render
- Build Command: `pip install -r requirements.txt`
- Start Command (usa Procfile automaticamente):
  - web: `gunicorn src.app:app`

## Limitações conhecidas
- PDFs somente-imagem (scans) não terão texto — este conversor **não** usa OCR. Para OCR, integrar `pytesseract` e Tesseract no sistema (não incluso para simplificar o deploy).
- A preservação de layout é **heurística**; o foco é deixar o conteúdo **editável**.

## Estrutura
```
/src
  app.py       # rotas Flask
  config.py
  utils.py
  pdf_ops.py   # dividir/mesclar
  doc_ops.py   # PDF -> DOCX (texto)
/static
/templates
Procfile
requirements.txt
```
