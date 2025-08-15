# PDF Suite (Flask + Celery)

Suite moderna para processar PDFs: **dividir**, **mesclar**, **comprimir** e **converter para DOCX** (com OCR opcional).

## Destaques
- Frontend responsivo (Grid/Flex), **modo claro/escuro** persistente e acessível (ARIA).
- **Validação** de tipo real de arquivo com `python-magic`.
- **Jobs assíncronos** com Celery + Redis.
- Progresso com **HTMX** (polling leve) e feedback visual.
- Dockerfile + docker-compose para subir tudo com um comando.

## Rodando com Docker
```bash
docker compose up --build
# web: http://localhost:5000
```

## Rodando local (sem Docker)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Inicie o Redis localmente, depois:
celery -A celery_app.celery worker --loglevel=INFO  # em um terminal
python app.py  # em outro terminal, http://localhost:5000
```

## Observações
- A compressão via PyPDF2 apenas reescreve o arquivo (não faz downsampling de imagens). Para compressão real, ajuste `ops/pdf_ops.py` para usar Ghostscript.
- OCR depende do Tesseract; o Dockerfile já inclui.
