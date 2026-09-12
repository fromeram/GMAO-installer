import React, { createContext, useState, useEffect, useContext } from "react";
import API_BASE_URL from "../apiConfig";

export const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  const fetchCurrentUser = async () => {
    try {
      const token = sessionStorage.getItem('access_token'); // ← CAMBIO 1: localStorage por sessionStorage
      if (!token) {
        setCurrentUser(null);
        return;
      }
      
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Token inválido');
      
      const user = await response.json();
      setCurrentUser(user);
    } catch (error) {
      console.error("Error:", error);
      logout();
    } finally {
      setAuthLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (username, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Credenciales incorrectas");
      }

      const data = await response.json();
      sessionStorage.setItem("access_token", data.access_token) // ← CAMBIO 2: localStorage por sessionStorage
      await fetchCurrentUser();
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    sessionStorage.removeItem("access_token") // ← CAMBIO 3: localStorage por sessionStorage
    setCurrentUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ 
      currentUser, 
      authLoading, 
      login, 
      logout 
    }}>
      {children}
    </AuthContext.Provider>
  );
};