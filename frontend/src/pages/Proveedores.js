// Proveedores.js
// Página para gestionar proveedores: crear y listar proveedores.
import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../apiConfig';

const Proveedores = () => {
  const [proveedores, setProveedores] = useState([]);
  const [nuevoProveedor, setNuevoProveedor] = useState({ nombre: '', company: '', phone: '' });
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchProveedores = async () => {
      try {
        const data = await fetchWithAuth('/suppliers');
        setProveedores(data);
      } catch (err) {
        console.error("Error al cargar los proveedores:", err);
        setError("Error al cargar los proveedores.");
      }
    };
    fetchProveedores();
  }, []);
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNuevoProveedor({ ...nuevoProveedor, [name]: value });
  };
  
  const handleAgregarProveedor = async (e) => {
    e.preventDefault();
    if (!nuevoProveedor.nombre || !nuevoProveedor.company || !nuevoProveedor.phone) {
      setError("Todos los campos son obligatorios.");
      return;
    }
    
    try {
      // CAMBIO: Asegurar que el Content-Type sea application/json
      const data = await fetchWithAuth('/suppliers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nuevoProveedor),
      });
      
      setProveedores([...proveedores, data]);
      setNuevoProveedor({ nombre: '', company: '', phone: '' });
      setError(null); // Limpiar mensaje de error si es exitoso
    } catch (err) {
      console.error("Error al agregar el proveedor:", err);
      setError("Error al agregar el proveedor: " + (err.message || "Error desconocido"));
    }
  };
  
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Gestión de Proveedores</h2>
      {error && <p className="text-red-500">{error}</p>}
      
      <form onSubmit={handleAgregarProveedor} className="flex flex-col gap-2 mb-4">
        <input
          type="text"
          name="nombre"
          value={nuevoProveedor.nombre}
          onChange={handleInputChange}
          placeholder="Nombre"
          required
          className="p-2 border rounded"
        />
        <input
          type="text"
          name="company"
          value={nuevoProveedor.company}
          onChange={handleInputChange}
          placeholder="Compañía"
          required
          className="p-2 border rounded"
        />
        <input
          type="text"
          name="phone"
          value={nuevoProveedor.phone}
          onChange={handleInputChange}
          placeholder="Teléfono"
          required
          className="p-2 border rounded"
        />
        <button type="submit" className="bg-green-600 text-white p-2 rounded">Agregar Proveedor</button>
      </form>
      
      <h3 className="text-lg font-bold mb-2">Lista de Proveedores</h3>
      {proveedores.length === 0 ? (
        <p>No hay proveedores registrados.</p>
      ) : (
        <ul className="list-disc ml-4">
          {proveedores.map((p) => (
            <li key={p.id}>
              {p.nombre} - {p.phone} - {p.company}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Proveedores;