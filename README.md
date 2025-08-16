
# Separador Digital Pro — Frontend moderno + Flask (Threads)

Interface moderna (dark/light), drag & drop, barra de progresso no upload, spinner durante processamento e downloads individual/ZIP. Backend em Flask com processamento em **thread de background** (sem Redis).

## Rodar local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
# abra http://localhost:5000/
```

## Deploy no Render
- `requirements.txt` já incluso
- `Procfile`: `web: gunicorn -c gunicorn_config.py app:app`
- Porta configurada em `gunicorn_config.py` (10000). O Render ignora e injeta a porta via env, mas mantemos o binding.

## Endpoints
- `POST /upload` → retorna `{ job_id }`
- `GET /status/<job_id>` → status + progress (%)
- `GET /list/<job_id>` → lista de PDFs gerados
- `GET /download/<job_id>` → ZIP
- `GET /download/<job_id>/<filename>` → arquivo individual
