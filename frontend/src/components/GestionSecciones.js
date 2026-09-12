// GestionSecciones.js
// Componente para la gestión (listar, agregar) de secciones.
// Se usa fetchWithAuth para interactuar con el backend.

import React, { useState, useEffect } from 'react';
import API_BASE_URL, { fetchWithAuth } from '../apiConfig';

const GestionSecciones = () => {
  const [secciones, setSecciones] = useState([]);
  const [newSection, setNewSection] = useState('');
  const [error, setError] = useState(null);

  // Se cargan las secciones al montar el componente
  useEffect(() => {
    const fetchSecciones = async () => {
      try {
        const data = await fetchWithAuth('/secciones');
        setSecciones(data);
      } catch (err) {
        setError('Error al cargar las secciones.');
      }
    };
    fetchSecciones();
  }, []);

  const addSection = async () => {
    if (!newSection) return;
    try {
      const response = await fetchWithAuth('/secciones', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: newSection }),
      });
      setSecciones([...secciones, response]);
      setNewSection('');
    } catch (err) {
      setError('Error al agregar la sección.');
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Gestión de Secciones</h2>
      {error && <p className="text-red-500">{error}</p>}
      <ul className="mb-4">
        {secciones.map((seccion, index) => (
          <li key={index} className="py-1 border-b">{seccion.nombre}</li>
        ))}
      </ul>
      <div className="flex gap-2">
        <input
          type="text"
          value={newSection}
          onChange={(e) => setNewSection(e.target.value)}
          placeholder="Nueva Sección"
          className="p-2 border rounded flex-grow"
        />
        <button onClick={addSection} className="bg-green-600 text-white p-2 rounded">Agregar Sección</button>
      </div>
    </div>
  );
};

export default GestionSecciones;
