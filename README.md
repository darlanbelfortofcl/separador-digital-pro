# PDF Tool (Flask) — Render Ready

> **Sem dor de cabeça no Render:** sem dependências de sistema (OCR removido por padrão), com **fallback síncrono** quando o Redis/Celery não estiver disponível.

## Recursos
- Dividir, mesclar e reescrever/comprimir PDFs (lossless)
- Converter PDF → DOCX via extração de texto (`pdfminer.six`)
- UI moderna, dark/light mode, arrastar & soltar, progresso
- Celery + Redis (opcional). Se indisponível, roda **síncrono** e responde já com link de download.

## Rodando localmente
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Sem Redis? Tudo funciona em modo síncrono.
# Com Redis/Celery?
# celery -A src.jobs.celery worker --loglevel=info

python -m src.app
```

## Deploy no Render
1. Faça push deste projeto no GitHub.
2. Render → **Web Service**:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn src.app:app`
   - Vars: (opcional) `REDIS_URL` para ativar fila assíncrona.
3. (Opcional) **Background Worker** para Celery:
   - Start: `celery -A src.jobs.celery worker --loglevel=info`
   - Mesmas variáveis de ambiente.
4. (Opcional) Provisione um Redis e use sua URL na var `REDIS_URL`.

### Saúde do serviço
- Verifique `/health` → `{ "ok": true, "celery_enabled": false|true }`.

## Observações
- Compressão real (com perda) exigiria Ghostscript (não incluso).
- OCR foi removido para evitar dependências de sistema (Poppler/Tesseract).

## Estrutura
```
/pdf-tool-fixed
├── src/{app.py,config.py,utils.py,pdf_ops.py,doc_ops.py,jobs.py,templates/}
├── static/{css,js}
├── requirements.txt
├── runtime.txt
├── Procfile
└── .env.example
```
