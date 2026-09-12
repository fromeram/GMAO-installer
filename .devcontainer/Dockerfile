# Usa una imagen base con Python y Node.js
FROM python:3.9-slim

# Instala Node.js (para el frontend)
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs

# Instala herramientas útiles
RUN apt-get install -y git

# Establece el directorio de trabajo
WORKDIR /workspace

# Copia los archivos de dependencias e instálalos
COPY backend/requirements.txt /workspace/backend/requirements.txt
RUN pip install -r /workspace/backend/requirements.txt

COPY frontend/package.json /workspace/frontend/package.json
COPY frontend/package-lock.json /workspace/frontend/package-lock.json
RUN cd /workspace/frontend && npm install

# Expone los puertos necesarios
EXPOSE 8000 3000