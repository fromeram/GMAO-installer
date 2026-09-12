# Stage 1: Build Frontend
FROM node:18-alpine AS build

WORKDIR /app

# Copiar los archivos de frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY frontend/. .
RUN npm run build --source-map=false

# Stage 2: Serve con Nginx
FROM nginx:latest

# Copiar los archivos construidos al directorio de Nginx
COPY --from=build /app/build /usr/share/nginx/html

# Copiar la configuración personalizada de Nginx
COPY frontend/nginx/default.conf /etc/nginx/conf.d/default.conf
