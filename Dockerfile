# Base Python
FROM python:3.10-slim

# Configurações básicas
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos do projeto
COPY .. /app

# Instala dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Define variáveis de ambiente (caso necessário)
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

# Comando para rodar a aplicação
CMD ["python", "main.py"]
