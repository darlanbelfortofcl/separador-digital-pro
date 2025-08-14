
# Separador Digital Pro — Modo Turbo (Editável)

PDF → DOCX **editável** (texto real) com **pdf2docx** em modo rápido (`layout_mode=loose`) e barra de progresso via **SSE**.
Divisão de PDF com ZIP final. UI moderna e responsiva.

## Rodar local
```
pip install -r requirements.txt
python app.py
# http://localhost:5000
```

## Render
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`

## Observação DOCX→PDF
Requer `docx2pdf` (Word/Office). Em Linux/Render, sem Word, essa rota pode não funcionar.
