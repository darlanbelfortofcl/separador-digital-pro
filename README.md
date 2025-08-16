
# Separador Digital Pro — Frontend fixado (sem loading infinito) + ZIP "Baixar Todos"

- Tema escuro/claro, drag & drop, barra de progresso real de upload.
- Spinner de processamento com timeout (180s) e mensagens de erro.
- Baixar **Todos (ZIP)** e **baixas individuais**.
- Backend Flask com processamento em thread.

## Local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
# http://localhost:5000/
```

## Render
Build: `pip install -r requirements.txt`  
Start: `gunicorn -c gunicorn_config.py app:app`
