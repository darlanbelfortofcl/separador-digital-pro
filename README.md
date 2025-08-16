
# Separador Digital Pro

Aplicativo web leve para dividir PDFs em **páginas individuais** ou **intervalos personalizados**. Otimizado para o **free tier do Render**.

## Funcionalidades
- Upload com **barra de progresso** e porcentagem.
- **Pré-visualização** do PDF (usa o visualizador nativo do navegador, sem libs pesadas).
- Divisão por **páginas individuais** ou **intervalos** (ex.: `1-3,5,7-9`).
- **Área restrita** com senha fixa (em variável de ambiente).
- **Dark mode automático** (`prefers-color-scheme`).
- Efeito visual de **"corte"** ao concluir (CSS animation).
- Rate limit de login (tentativas por janela de tempo).

## Stack
- Backend: **Flask**
- PDF: **PyPDF2**
- Frontend: **HTML/CSS** + **JS vanilla** (leve)
- Servidor: **gunicorn**

## Rodando localmente
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

export SECRET_KEY="algumseguro"
export SENHA_ADMIN="sua_senha"
# Opcional:
export MAX_CONTENT_LENGTH_MB=32
export LOGIN_WINDOW_MIN=15
export LOGIN_MAX_ATTEMPTS=5

python app.py
# abra http://localhost:5000
```

## Deploy no Render (automático)
1. **Envie** este projeto para um repositório no **GitHub**.
2. No Render, crie um **Web Service** → **Build Command**: `pip install -r requirements.txt` (já definido em `render.yaml`).
3. **Start Command**: `gunicorn app:app --timeout 120 --workers 1 --threads 2` (também em `render.yaml`).
4. Configure as **variáveis de ambiente**:
   - `SECRET_KEY` (pode usar *Generate*).
   - `SENHA_ADMIN` (defina sua senha).
   - (opcionais) `MAX_CONTENT_LENGTH_MB`, `LOGIN_WINDOW_MIN`, `LOGIN_MAX_ATTEMPTS`.
5. Conecte ao repositório e **deploy**.

### Dicas para o plano gratuito
- **Limite de tamanho**: por padrão 32 MB (ajuste `MAX_CONTENT_LENGTH_MB` se necessário).
- **Timeout**: usamos `--timeout 120` no gunicorn. PDFs grandes podem demorar; se necessário, divida em intervalos menores.
- **Memória**: processamento é feito **em memória** (sem gravar no disco), adequado a 512MB.
- **Workers/threads**: `1` worker e `2` threads para manter o consumo baixo.

## Segurança
- Senha do admin em `SENHA_ADMIN` (variável de ambiente).
- Rate limit de login: máx. tentativas por janela (padrão: 5 em 15 min). Baseado em IP.
- CSRF básico para POSTs.
- Cookies `HttpOnly` e `SameSite=Lax`.

## Como usar
1. Faça login com a senha.
2. Selecione o PDF (a pré-visualização aparece abaixo).
3. Escolha **Páginas individuais** ou **Intervalos** (ex.: `1-3,5,7-9`).
4. Clique em **Separar**.
5. O download será iniciado automaticamente (um PDF único ou um `.zip` com múltiplos PDFs).

## Estrutura
```
.
├── app.py
├── requirements.txt
├── Procfile
├── render.yaml
├── templates
│   ├── layout.html
│   ├── login.html
│   └── index.html
├── static
│   ├── css/styles.css
│   ├── js/app.js
│   └── img/favicon.svg
└── README.md
```

## Licença
MIT
