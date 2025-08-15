# PDF Multi Splitter

App Flask para dividir vários PDFs, mantendo nomes originais.

## Local
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Render
- Adicione este código ao GitHub
- Configure como Web Service Python
- Build Command: `pip install -r requirements.txt`
- Start Command: deixado no Procfile (`gunicorn app:app`)
