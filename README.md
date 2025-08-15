# Multi PDF Splitter (nomes preservados)

Web app (Flask) para enviar **vários PDFs**, dividir cada um em páginas mantendo o **nome original**, e baixar um **ZIP** organizado com uma pasta por PDF.

## Como usar (local)
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
# abra http://localhost:5000
```

## Rotas
- `GET  /` — formulário simples com upload múltiplo
- `POST /split` — envia 1..N PDFs (campo `arquivos`) e retorna `job_id`
- `GET  /status/<job_id>` — progresso `{status, progress, total}`
- `GET  /download?path=...` — baixa o ZIP final (validação de caminho habilitada)
