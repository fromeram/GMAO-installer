// frontend/src/config.js
/**
 * Configuración central para el frontend de GMAO.
 * Obtiene valores de variables de entorno.
 */

// URL base de la API
const API_BASE_URL = process.env.REACT_APP_API_URL || "/api";

// Configuración de timeouts para peticiones
const REQUEST_TIMEOUT = parseInt(process.env.REACT_APP_REQUEST_TIMEOUT || "30000", 10);

// Configuración de autenticación
const TOKEN_STORAGE_KEY = "access_token";

// Tiempo de refresco de datos en aplicación (ms)
const DATA_REFRESH_INTERVAL = parseInt(process.env.REACT_APP_REFRESH_INTERVAL || "60000", 10);

export { 
    API_BASE_URL,
    REQUEST_TIMEOUT,
    TOKEN_STORAGE_KEY,
    DATA_REFRESH_INTERVAL
};
