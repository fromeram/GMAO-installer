// src/aiApiConfig.js

import axios from 'axios';

// Crear una instancia de axios específicamente para los endpoints de IA
const aiApi = axios.create({
  baseURL: '/api/ai', // URL base para las rutas de IA que creamos
});

// Interceptor para añadir el token de autenticación a cada petición de IA
aiApi.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    console.log(`[DEBUG AI] Enviando ${config.method.toUpperCase()} a: <span class="math-inline">\{config\.baseURL\}</span>{config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar respuestas de la API de IA
aiApi.interceptors.response.use(
  (response) => {
    return response; // Si es exitosa, la devuelve
  },
  (error) => {
    // Si el token es inválido o ha expirado (error 401)
    if (error.response && error.response.status === 401) {
      console.error("Error 401 en API de IA. Redirigiendo al login.");
      sessionStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Exportar la nueva instancia de axios para IA
export default aiApi;