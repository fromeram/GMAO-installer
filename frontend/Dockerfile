# frontend/Dockerfile (Versión Multi-etapa para Nginx)

# --- Etapa 1: Construcción de la App React ---
FROM node:18-alpine AS build-stage
WORKDIR /app

# Variables de entorno para la construcción de React
ENV REACT_APP_API_URL=/api

# Copiar archivos de paquetes
COPY frontend/package.json frontend/package-lock.json ./

# Instalar dependencias
RUN npm install --legacy-peer-deps

# Copiar el código fuente de frontend
COPY frontend/. .

# Construir la aplicación para producción
RUN npm run build --source-map=false

# --- Etapa 2: Servidor Nginx ---
FROM nginx:stable-alpine

# Copiar los archivos estáticos construidos desde la etapa anterior
COPY --from=build-stage /app/build /usr/share/nginx/html

# Eliminar configuración por defecto para usar la montada por volumen
RUN rm -f /etc/nginx/conf.d/default.conf

# Exponer puerto y comando por defecto de Nginx
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
