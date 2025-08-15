# Divisor de PDFs (múltiplos arquivos, UI moderna)

- Envie vários PDFs de uma vez
- Lista os arquivos selecionados (ícone + nome)
- Divide cada PDF em páginas, preservando o nome original
- Gera um ZIP com pastas por arquivo
- Assíncrono com status e progresso
- Pronto para rodar local e no Render

## Rodando local
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
# abra http://localhost:5000
```

## Deploy no Render
- Build Command: `pip install -r requirements.txt`
- Start Command: deixe vazio (usa o Procfile: `gunicorn app:app`)
