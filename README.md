# Separador Digital Pro — Modo Turbo (Editável)

PDF → DOCX **editável** (texto real) com **pdf2docx** em modo rápido (`layout_mode=loose`) e barra de progresso via **SSE**.
Divisão de PDF com ZIP final. UI moderna e responsiva.

## Rodar local
```bash
python -m venv .venv
# Windows:
#   .venv\Scripts\activate
# macOS/Linux:
#   source .venv/bin/activate
pip install -r requirements.txt
python app.py
# abra: http://localhost:5000
```

## Produção (Render/Heroku/etc.)
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`

## Observação DOCX→PDF
- Requer `docx2pdf` com Microsoft Word instalado (Windows/macOS).
- Em Linux, a rota retornará erro amigável.

## Segurança
- Downloads validados para garantir que o arquivo esteja **dentro de** `outputs/`.
- Nomes de arquivos tornam-se únicos com `uuid` e `secure_filename`.

## Limpeza automática
- Um job periódico (APScheduler) apaga itens antigos de `uploads/` e `outputs/`.
- Variáveis de ambiente:
  - `CLEANUP_ENABLED=1`
  - `CLEANUP_AGE_HOURS=24`
  - `CLEANUP_INTERVAL_MINUTES=30`

## Testes
```bash
pytest -q
```

## Estrutura
```
app.py
config.py
jobs.py
file_utils.py
pdf_ops.py
conversor.py
cleanup.py
tests/
  ├─ test_paths.py
  └─ test_allowed_file.py
```

