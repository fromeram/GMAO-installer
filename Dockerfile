FROM node:18-alpine as build

WORKDIR /app

# Copiar solo los archivos de dependencias primero
COPY frontend/package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto de la aplicación
COPY frontend/. .

# Construir la aplicación
RUN npm run build --source-map=false

# Configuración de nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
