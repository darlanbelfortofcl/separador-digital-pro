
# Separador Digital Pro (Flask + RQ)

Divisor de PDFs com upload múltiplo, processamento **assíncrono** (RQ/Redis), interface moderna (dark/light), e deploy pronto para **Render**.

## Requisitos
- Python 3.11+
- Redis (ex.: Render Redis, Upstash, etc.)

## Variáveis de Ambiente
- `SECRET_KEY` (recomendado)
- `REDIS_URL` (obrigatório em produção)
- `RQ_QUEUE_NAME` (opcional, default: `pdf_tasks`)
- `MAX_CONTENT_LENGTH` (opcional, default: 52428800 = 50MB)
- `CLEANUP_TTL_HOURS` (opcional, default: 12)

## Desenvolvimento local
1) Crie o ambiente e instale dependências:
   - `python -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
2) Suba um Redis local e defina `REDIS_URL`:
   - `export REDIS_URL=redis://localhost:6379/0`
3) Rode o servidor:
   - `python app.py`
4) Em outro terminal, rode o worker:
   - `rq worker --url $REDIS_URL pdf_tasks`

## Produção (Render)
- **Web Service**
  - Build: `pip install -r requirements.txt`
  - Start: `gunicorn -c gunicorn_config.py app:app`
- **Worker Service**
  - Build: `pip install -r requirements.txt`
  - Start: `rq worker --url $REDIS_URL $RQ_QUEUE_NAME`

Defina `REDIS_URL` apontando para seu Redis gerenciado (Render Redis, Upstash, etc.).

## Endpoints
- `POST /upload` → retorna `{ "job_id": "<id>" }`
- `GET /status/<job_id>` → retorna `{ "status": "...", "progress": 0-100, "download_url": "/download/<job_id>"? }`
- `GET /download/<job_id>` → baixa `pdfs_divididos.zip`
