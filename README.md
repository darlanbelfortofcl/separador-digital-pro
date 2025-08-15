# PDF Tool (Flask + Celery)

Projeto pronto para GitHub e deploy no Render.

## Estrutura
```
/pdf-tool
├── .github/workflows/python-app.yml
├── src/
│   ├── app.py
│   ├── config.py
│   ├── jobs.py
│   ├── pdf_ops.py
│   ├── doc_ops.py
│   ├── utils.py
│   └── templates/
├── static/
│   ├── css/base.css
│   └── js/{theme.js,uploader.js,actions.js}
├── requirements.txt
├── runtime.txt
├── Procfile
├── .env.example
└── README.md
```

## Como rodar localmente
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Inicie o worker Celery (requer Redis em execução)
celery -A src.jobs.celery worker --loglevel=info

# Em outro terminal, rode o Flask
python -m src.app
# ou: FLASK_APP=src.app flask run
```

## Deploy no Render
1. Crie um repositório no GitHub e envie estes arquivos.
2. No Render, crie **Web Service** conectado ao seu repositório.
3. Build Command: `pip install -r requirements.txt`
4. Start Command (já no Procfile): `web: gunicorn src.app:app`
5. Crie um **Background Worker** para o Celery com o comando:
   ```
   celery -A src.jobs.celery worker --loglevel=info
   ```
6. Em **Environment** adicione as variáveis do `.env.example` (principal: `REDIS_URL`).
7. Opcional: adicione Redis (Render oferece um add-on) e use sua URL no `REDIS_URL`.

> Observação: O HTMX é carregado via CDN no HTML; **não coloque** no `requirements.txt`.

## Funcionalidades
- Dividir PDFs
- Mesclar PDFs
- Comprimir (reescrita simples)
- Converter PDF → DOCX (OCR opcional — requer Tesseract instalado no sistema)

## Notas de produção
- Compressão efetiva de imagens requer Ghostscript; a função atual reescreve o PDF.
- Se usar OCR, instale `tesseract-ocr` (em Docker/Ubuntu: `apt-get install -y tesseract-ocr`).

## Testes
Há uma suíte mínima para CI no GitHub Actions.
