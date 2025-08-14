# Separador Digital Pro (deploy-ready)

- Flask + Gunicorn
- Rotas:
  - `/` interface web
  - `/process` dividir PDF (campo `arquivo_pdf`)
  - `/convert` converter (campo `arquivo` + `mode`)
  - `/stream?job=...` SSE de progresso
  - `/download?path=...` baixar resultado

## Executar local
```
pip install -r requirements.txt
python app.py
```

## Deploy (Render)
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
