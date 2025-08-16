
# Separador Digital Pro — Multi PDF
- Login (senha fixa): `29031984bB@G`
- Upload múltiplo de PDFs, divisão por **todas as páginas** ou por **intervalos personalizados**.
- Download final em **ZIP** (organizado por arquivo).
- Modo escuro/claro com persistência.
- Barra de progresso de upload + modal de sucesso/erro.
- Favicon incluso.

## Executar localmente
```bash
pip install -r requirements.txt
python app.py
```
Abra http://127.0.0.1:5000

## Deploy no Render
- `render.yaml` e `Procfile` prontos.
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app --timeout 120 --workers 1 --threads 2`
- Python: `python-3.11.9` via `runtime.txt`.

## Observações
- Intervalos: use formato `1-3,5,7-9` (1-based). 
- Se nenhum intervalo válido for informado no modo "intervalos", o arquivo é ignorado.
