
# Separador Digital Pro — Multi PDF (versão robusta)

- Login (senha fixa): `29031984bB@G`
- Upload múltiplo de PDFs
- Dois modos: **Dividir tudo** (cada página) ou **Intervalos** (1-3,5,7-9)
- Gera ZIP com subpastas por arquivo + **relatorio.txt** com sucessos e erros
- Tema escuro/claro com persistência
- Barra de progresso + modal de sucesso/erro
- Favicon (SVG)

## Executar localmente
```bash
pip install -r requirements.txt
python app.py
```
Acesse http://127.0.0.1:5000

## Deploy no Render
- `render.yaml` e `Procfile` prontos.
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app --timeout 120 --workers 1 --threads 2`
- Python: `python-3.11.9` via `runtime.txt`.

## Notas de robustez
- PDF criptografado: tenta abrir sem senha; se protegido, o arquivo é ignorado e anotado no `relatorio.txt`.
- Intervalos inválidos: arquivo é ignorado e anotado no relatório.
- Se nenhum arquivo for gerado, a resposta é erro 400 com mensagem clara no modal.
