# Separador Digital Pro

Ferramenta para conversão, divisão e compressão de PDFs e outros formatos.

## Requisitos
- Python 3.9 ou superior
- pip (gerenciador de pacotes Python)
- Tesseract OCR instalado (para funções OCR)
- Ghostscript instalado (para compressão de alta qualidade)

## Passo a passo de instalação
1. Extraia o arquivo ZIP em uma pasta de sua escolha.
2. Abra o terminal (Prompt de Comando ou PowerShell) nessa pasta.
3. Crie e ative um ambiente virtual (opcional, mas recomendado):
   Windows:
       python -m venv venv
       venv\Scripts\activate
   Linux/Mac:
       python3 -m venv venv
       source venv/bin/activate

4. Instale as dependências:
       pip install -r requirements.txt

5. Execute o sistema:
       python app.py

6. Abra no navegador:
       http://localhost:5000

## Observações
- Coloque seus arquivos para processar no navegador, eles serão processados localmente.
- Para OCR, instale o Tesseract OCR e configure-o no PATH do sistema.
- Para compressão otimizada, instale o Ghostscript.
