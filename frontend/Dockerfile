# frontend/Dockerfile - Multi-stage Production Build for Nginx
FROM node:18-alpine AS build-stage
WORKDIR /app

ENV REACT_APP_API_URL=/api

# Copiar dependencias
COPY package.json package-lock.json ./
RUN npm install --legacy-peer-deps

# Copiar código fuente
COPY . .

# Compilar para producción (sin source-maps para proteger código y aligerar peso)
RUN npm run build --source-map=false

# --- Etapa 2: Servidor Web Nginx de Producción ---
FROM nginx:stable-alpine

# Copiar estáticos compilados
COPY --from=build-stage /app/build /usr/share/nginx/html

# Configuración por defecto de Nginx para SPA + Proxy API
RUN cat << 'EOF' > /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    client_max_body_size 50M;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
EOF

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
