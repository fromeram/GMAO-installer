// Almacen.js
// Componente para la gestión del almacén: agregar productos y comparar precios.

import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../apiConfig';

const Almacen = () => {
  const [productos, setProductos] = useState([]);
  const [nuevoProducto, setNuevoProducto] = useState({
    nombre: '',
    cantidad: '',
    ubicacion: '',
    precio: '',
    proveedor: '',
  });
  const [compararPrecios, setCompararPrecios] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProductos = async () => {
      try {
        const data = await fetchWithAuth('/productos');
        setProductos(data);
      } catch (err) {
        console.error('Error al cargar los productos:', err);
        setError('Error al cargar los productos.');
      }
    };
    fetchProductos();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNuevoProducto({ ...nuevoProducto, [name]: value });
  };

  const handleAgregarProducto = async (e) => {
    e.preventDefault();
    try {
      const data = await fetchWithAuth('/productos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre: nuevoProducto.nombre,
          cantidad: parseInt(nuevoProducto.cantidad, 10),
          ubicacion: nuevoProducto.ubicacion,
          precio: parseFloat(nuevoProducto.precio),
          proveedor: nuevoProducto.proveedor
        }),
      });
      setProductos([...productos, data]);
      setNuevoProducto({ nombre: '', cantidad: '', ubicacion: '', precio: '', proveedor: '' });
    } catch (err) {
      console.error('Error al agregar el producto:', err);
      setError('Error al agregar el producto.');
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Gestión del Almacén</h2>
      {error && <p className="text-red-500">{error}</p>}
      <button
        onClick={() => setCompararPrecios(!compararPrecios)}
        className="mb-4 bg-blue-600 text-white p-2 rounded"
      >
        {compararPrecios ? 'Volver al Stock' : 'Comparar Precios'}
      </button>
      <form onSubmit={handleAgregarProducto} className="flex flex-col gap-2 mb-4">
        <input type="text" name="nombre" value={nuevoProducto.nombre} onChange={handleInputChange} placeholder="Nombre" required className="p-2 border rounded" />
        <input type="number" name="cantidad" value={nuevoProducto.cantidad} onChange={handleInputChange} placeholder="Cantidad" required className="p-2 border rounded" />
        <input type="text" name="ubicacion" value={nuevoProducto.ubicacion} onChange={handleInputChange} placeholder="Ubicación" required className="p-2 border rounded" />
        <input type="number" step="0.01" name="precio" value={nuevoProducto.precio} onChange={handleInputChange} placeholder="Precio" required className="p-2 border rounded" />
        <input type="text" name="proveedor" value={nuevoProducto.proveedor} onChange={handleInputChange} placeholder="Proveedor" required className="p-2 border rounded" />
        <button type="submit" className="bg-green-600 text-white p-2 rounded">Agregar Producto</button>
      </form>
      <h3 className="font-bold mb-2">Lista de Productos</h3>
      <ul>
        {productos.map((producto) => (
          <li key={producto.id} className="py-1 border-b">
            {producto.nombre} - {producto.cantidad} unidades en {producto.ubicacion} (${producto.precio}) - Proveedor: {producto.proveedor}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Almacen;
