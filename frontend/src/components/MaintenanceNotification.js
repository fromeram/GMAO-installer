// components/MaintenanceNotification.js
import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../apiConfig';
import { useAuth } from '../contexts/AuthContext';

const MaintenanceNotification = () => {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const { currentUser } = useAuth();

  // Función para verificar mantenimientos pendientes
  const checkPendingMaintenance = async () => {
    try {
      const response = await fetchWithAuth('/mantenimiento-preventivo/pending');
      if (response.length > 0) {
        setNotifications(response);
        setIsOpen(true);
      }
    } catch (error) {
      console.error('Error al verificar mantenimientos:', error);
    }
  };

  // Verificar cada 5 minutos
  useEffect(() => {
    if (currentUser) {
      checkPendingMaintenance();
      const interval = setInterval(checkPendingMaintenance, 5 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [currentUser]);

  const handleMarkComplete = async (maintenanceId) => {
    try {
      await fetchWithAuth(`/mantenimiento-preventivo/${maintenanceId}/complete`, {
        method: 'PUT'
      });
      setNotifications(notifications.filter(n => n.id !== maintenanceId));
      if (notifications.length <= 1) setIsOpen(false);
    } catch (error) {
      console.error('Error al marcar como completado:', error);
    }
  };

  if (!isOpen || notifications.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="bg-white rounded-lg shadow-xl p-4 max-w-sm w-full">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Mantenimientos Pendientes
          </h3>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            ×
          </button>
        </div>
        <div className="space-y-4">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className="border-b pb-3 last:border-b-0 last:pb-0"
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-medium text-gray-900">
                    {notification.title}
                  </p>
                  <p className="text-sm text-gray-600">
                    Máquina: {notification.machine_name}
                  </p>
                  <p className="text-sm text-gray-600">
                    Fecha programada: {new Date(notification.next_maintenance_date).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => handleMarkComplete(notification.id)}
                  className="px-3 py-1 bg-green-500 text-white rounded-md text-sm hover:bg-green-600"
                >
                  Completar
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MaintenanceNotification;