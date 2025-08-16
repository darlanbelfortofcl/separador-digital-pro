# Separador Digital Pro

Flask minimalista para divisão de PDFs por páginas/intervalos,
com login via senha em variável de ambiente e barra de progresso (SSE).
Leve para rodar no plano gratuito do Render.

## Variáveis de ambiente
- `SECRET_KEY` (obrigatória em produção)
- `SENHA_ADMIN` (obrigatória) – senha única de acesso ao painel
- `UPLOAD_FOLDER` (opcional; padrão `uploads`)
- `OUTPUT_FOLDER` (opcional; padrão `outputs`)
- `PORT` (Render define automaticamente)

## Como rodar localmente
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY=um-segredo
export SENHA_ADMIN=trocar
python -m app
```

## Deploy no Render (Web Service)
1. Faça push deste projeto para um repositório Git.
2. No Render, crie um **Web Service** apontando para o repositório.
3. **Runtime**: Python 3.11+
4. **Start command**: `gunicorn 'app:create_app()'`
5. Configure **Environment Variables**:
   - `SECRET_KEY` (valor longo e aleatório)
   - `SENHA_ADMIN`
6. Habilite o autoscaling **OFF** (plano free) e região próxima.
7. Deploy!

## Observações de Otimização
- Uso de **PyPDF2** (leve) e split direto em disco, evitando alto consumo de RAM.
- SSE com intervalos curtos e payload pequeno.
- Thumbnails simulados com `<embed>` escalado (sem PDF.js).
- Limpeza automática pode ser adicionada via cron externo do Render (opcional).

## Estrutura
```
/app
  /static
  /templates
  __init__.py
  routes.py
  utils.py
requirements.txt
Procfile
```
