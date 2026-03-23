# Imagem base Python oficial
FROM python:3.11-slim

# Diretório de trabalho no container
WORKDIR /app

# Instalar dependências de sistema (necessárias para o Playwright/Chromium)
RUN apt-get update && apt-get install -y \
    wget gnupg curl unzip tzdata libgconf-2-4 libgtk-3-0 libxss1 libnss3 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requerimentos primeiro (aproveita cache do Docker)
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Instalação do Chromium via Playwright (essencial pro scraper SP/RJ)
RUN playwright install chromium
RUN playwright install-deps

# Copia todo o projeto para o diretório
COPY . .

# Expõe a porta que o Flask vai rodar
EXPOSE 5000

# Comando para iniciar o servidor web usando Gunicorn
# Timeout de 120s para permitir consultas longas de Scraping
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "3", "app:app"]