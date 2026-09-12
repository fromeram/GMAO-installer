import React, { createContext, useState, useEffect, useContext } from "react";
import API_BASE_URL from "../apiConfig";

export const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  const fetchCurrentUser = async () => {
    setAuthLoading(true);
    try {
      const token = sessionStorage.getItem('access_token');
      if (!token) {
        setCurrentUser(null);
        return;
      }
      
      const response = await fetch(`${API_BASE_URL || '/api'}/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('La sesión ha expirado');
      
      const user = await response.json();
      setCurrentUser(user);
    } catch (error) {
      console.error("Error al obtener el usuario:", error);
      logout();
    } finally {
      setAuthLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  // ✅ --- FUNCIÓN DE LOGIN CORREGIDA PARA ENVIAR JSON ---
  const login = async (username, password) => {
    try {
      const response = await fetch(`${API_BASE_URL || '/api'}/token`, {
        method: "POST",
        headers: {
          // Volvemos a usar JSON, que es lo que tu backend espera
          "Content-Type": "application/json",
        },
        // Enviamos el cuerpo como un string JSON
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Credenciales incorrectas");
      }

      const data = await response.json();
      sessionStorage.setItem("access_token", data.access_token);
      await fetchCurrentUser();

    } catch (error) {
      console.error("Error en el proceso de login:", error);
      throw error;
    }
  };

  const logout = () => {
    sessionStorage.removeItem("access_token");
    setCurrentUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ currentUser, authLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};