// frontend/src/apiConfig.js (Versión Final y Unificada)

import axios from 'axios';

// --- LÓGICA ANTIGUA (Se mantiene intacta para que el resto del GMAO funcione) ---

const API_BASE_URL = process.env.REACT_APP_API_URL || "/api";

export const fetchWithAuth = async (endpoint, options = {}) => {
  try {
    // Usamos 'access_token' como en tu código original
    const token = sessionStorage.getItem('access_token');
    
    if (!token && !endpoint.includes('/login')) { // No redirigir si ya estamos en login
      window.location.href = '/login';
      return;
    }

    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${API_BASE_URL}${normalizedEndpoint}`;

    const requestOptions = {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    if (requestOptions.body && typeof requestOptions.body === 'object') {
      requestOptions.body = JSON.stringify(requestOptions.body);
    }

    const response = await fetch(url, requestOptions);

    if (options.method === 'DELETE' && response.status === 204) {
      return { success: true };
    }
    // Para descargas de archivos, devolver la respuesta directamente
    if (endpoint.includes('/download/')) {
      if (!response.ok) {
        throw new Error(`Error del servidor: ${response.status}`);
      }
      return response; // Devolver response directamente para archivos
    }
    // Para respuestas JSON normales (código existente...)

    const responseText = await response.text();
    let data;
    try {
      data = responseText ? JSON.parse(responseText) : {};
    } catch (e) {
      data = { text: responseText, parseError: true };
    }

    if (!response.ok) {
      const errorMessage = data.message || data.detail || `Error del servidor: ${response.status}`;
      if (response.status === 401) {
        sessionStorage.removeItem('access_token');
        window.location.href = '/login';
      }
      throw new Error(errorMessage);
    }
    return data;
  } catch (error) {
    console.error('Error en la petición (fetchWithAuth):', error);
    throw error;
  }
};

// Mantenemos las otras exportaciones originales
export default API_BASE_URL;

const PROXY_URL = process.env.REACT_APP_PROXY_URL || "http://192.168.1.62:5000";

export const callExtractionProxy = async (file_path, model = "gemma3:27b") => {
    // ... (tu código original aquí sin cambios)
};

export const processDocumentWithAI = async (documentId) => {
    // ... (tu código original aquí sin cambios)
};


// --- LÓGICA NUEVA (Se añade al final del fichero) ---

// 1. Crear la instancia de axios para los nuevos componentes de IA
const axiosInstance = axios.create({
  baseURL: '/api', // Usamos la URL base general
});

// 2. Interceptor para AÑADIR el token (usando la clave correcta 'access_token')
axiosInstance.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 3. Interceptor para MANEJAR errores 401
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.error("Error 401 detectado por Axios. Redirigiendo al login.");
      sessionStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 4. Exportamos la instancia de axios como un objeto con nombre llamado 'api'
export const api = axiosInstance;

// Función especial para descargar archivos con autenticación
export const downloadFile = async (endpoint, filename = 'documento') => {
  try {
    const token = sessionStorage.getItem('access_token');
    if (!token) {
      window.location.href = '/login';
      return;
    }

    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${API_BASE_URL}${normalizedEndpoint}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      }
    });

    if (response.status === 401) {
      sessionStorage.removeItem('access_token');
      window.location.href = '/login';
      return;
    }

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    
    // Limpiar
    window.URL.revokeObjectURL(downloadUrl);
    document.body.removeChild(link);
  } catch (error) {
    console.error('Error downloading file:', error);
    throw error;
  }
};