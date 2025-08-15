FROM python:3.11-slim

# Dependências de sistema para OCR e PDF rasterization
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \    poppler-utils \    libmagic1 \    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_DEBUG=0
ENV PORT=5000

# Gunicorn for prod
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
