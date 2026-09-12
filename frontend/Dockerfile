# frontend/Dockerfile (Versión Multi-etapa para Nginx)

# --- Etapa 1: Construcción de la App React ---
    FROM node:18-alpine AS build-stage
    WORKDIR /app
    
    # Copiar archivos de paquetes (Asumiendo build desde gmao-project, ajusta si es necesario)
    # Si el contexto en docker-compose.yml es '.', las rutas son relativas a eso
    COPY frontend/package.json frontend/package-lock.json ./
    
    # Instalar dependencias
    RUN npm install --legacy-peer-deps
    
    # Copiar el código fuente de frontend
    COPY frontend/. .
    
    # Construir la aplicación para producción
    # Quita el sleep y cualquier ENV de desactivación de ESLint
    RUN npm run build --source-map=false
    #RUN CI=true npm run build --source-map=false
    
    # --- Etapa 2: Servidor Nginx ---
    FROM nginx:stable-alpine

    # Copiar los archivos estáticos construidos desde la etapa anterior
    COPY --from=build-stage /app/build /usr/share/nginx/html

    # Copiar tu configuración personalizada de Nginx (CORREGIR RUTA)
    # Asegúrate que el archivo existe en frontend/nginx/nginx.conf
    #COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
    RUN rm -f /etc/nginx/conf.d/default.conf

    # Exponer puerto y comando por defecto de Nginx
    EXPOSE 80
    CMD ["nginx", "-g", "daemon off;"]

#FROM node:18-alpine

#WORKDIR /app

#COPY package.json package-lock.json ./

#RUN npm install

#COPY . .

#RUN npm run build --source-map=false

# Salir exitosamente después de la construcción
#CMD ["tail", "-f", "/dev/null"]
