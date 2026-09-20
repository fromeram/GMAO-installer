// UserManagement.js
// Componente para la gestión de usuarios: listar y crear nuevos usuarios.

import React, { useState, useEffect } from "react";
import API_BASE_URL, { fetchWithAuth } from "../apiConfig";

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [newUser, setNewUser] = useState({ username: "", password: "", role_id: "" });
  const [error, setError] = useState(null);

  // Cargar roles y usuarios al montar el componente
  useEffect(() => {
    const fetchRoles = async () => {
      try {
        const data = await fetchWithAuth("/roles");
        setRoles(data);
      } catch (err) {
        setError("Error al cargar los roles.");
      }
    };

    const fetchUsers = async () => {
      try {
        const data = await fetchWithAuth("/users");
        setUsers(data);
      } catch (err) {
        setError("Error al cargar los usuarios.");
      }
    };

    fetchRoles();
    fetchUsers();
  }, []);

  const handleCreateUser = async () => {
    if (!newUser.username || !newUser.password || !newUser.role_id) {
      setError("Todos los campos son obligatorios.");
      return;
    }

    try {
      const response = await fetchWithAuth("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newUser),
      });
      setUsers([...users, response]);
      setNewUser({ username: "", password: "", role_id: "" });
    } catch (err) {
      setError("Error al crear el usuario.");
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Gestión de Usuarios</h2>
      {error && <p className="text-red-500">{error}</p>}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Nombre de usuario"
          value={newUser.username}
          onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
          className="p-2 border rounded mr-2"
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={newUser.password}
          onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
          className="p-2 border rounded mr-2"
        />
        <select
          value={newUser.role_id}
          onChange={(e) => setNewUser({ ...newUser, role_id: e.target.value })}
          className="p-2 border rounded mr-2"
        >
          <option value="">Seleccionar Rol</option>
          {roles.map((role) => (
            <option key={role.id} value={role.id}>
              {role.nombre}
            </option>
          ))}
        </select>
        <button onClick={handleCreateUser} className="bg-blue-600 text-white p-2 rounded">
          Crear Usuario
        </button>
      </div>
      <h3 className="font-bold mb-2">Lista de Usuarios</h3>
      <ul>
        {users.map((user) => (
          <li key={user.id} className="py-1 border-b">
            {user.username}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default UserManagement;