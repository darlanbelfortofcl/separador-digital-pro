
# Separador Digital Pro (UI moderna + funcional)

Ferramenta web para **converter** (PDF ↔ DOCX) e **dividir PDF** em páginas, com:
- **Barra de progresso em tempo real** (SSE)
- **Interface moderna e responsiva (mobile first)**
- **Rastro de pontinhos brilhantes** no cursor
- **Download do resultado** (arquivo único ou ZIP)
- **Deploy fácil no Render**

## ▶️ Rodar local
```bash
pip install -r requirements.txt
python app.py
```
Abra: http://localhost:5000

## ☁️ Deploy no Render
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

## Rotas (API)
- `POST /convert` — `mode` (pdf2docx|docx2pdf), `arquivo` (file)
- `POST /process` — `arquivo_pdf` (file), `qualidade` (low|ebook|high)
- `GET /stream?job=ID` — SSE do progresso
- `GET /download?path=...` — baixar

© 2025 Separador Digital Pro
