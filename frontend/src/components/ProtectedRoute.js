import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const ProtectedRoute = ({ children }) => {
  const { authLoading } = useAuth();
  const token = sessionStorage.getItem('access_token'); // 👈 Verifica directamente el token

  if (authLoading) return <div>Cargando...</div>;
  if (!token) return <Navigate to="/login" replace />; // 👈 Redirige sin depender de currentUser

  return children;
};

export default ProtectedRoute;