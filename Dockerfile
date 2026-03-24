# Imagem base oficial do Playwright da Microsoft (já contém todas as dependências do OS para navegadores)
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Diretório de trabalho no container
WORKDIR /app

# Copia os arquivos de requerimentos primeiro (aproveita cache do Docker)
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Instalação apenas do Chromium via Playwright (sem dependências de OS adicionais)
RUN playwright install chromium

# Copia todo o projeto para o diretório
COPY . .

# Comando para iniciar o servidor web usando Gunicorn vinculado à porta dinâmica do Render
# Timeout de 120s para permitir consultas longas de Scraping
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 120 --workers 3 app:app"]