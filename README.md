# PDF Toolkit (Render-ready)
Flask app para **converter PDF → DOCX editável**, **dividir** e **mesclar** PDFs. Pronto para deploy no Render.

## Rodar local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.app
# ou
gunicorn src.app:app -b 0.0.0.0:5000
```
Acesse: http://localhost:5000

## Deploy no Render
1) Crie um Web Service apontando para este repositório.
2) Build command: `pip install -r requirements.txt`
3) **Start command**: deixe em branco (Render usa `Procfile`) ou defina **exatamente**: `gunicorn src.app:app`
4) Deploy.
5) Teste o healthcheck: `/health` → deve retornar `{"status":"ok"}`.

### Observações
- Sem `pdf2image` e sem `python-magic` (evita dependências de sistema).
- Conversão focada em conteúdo **editável**; PDFs apenas-imagem não terão texto (sem OCR).
