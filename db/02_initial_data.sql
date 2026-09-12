-- ==============================================================================
-- GMAO SYSTEM - Datos Base del Sistema
-- ==============================================================================

-- 1. Roles del sistema esenciales
INSERT INTO roles (id, nombre) VALUES 
    (1, 'Administrador'),
    (2, 'Jefe de Mantenimiento'),
    (3, 'Jefe de Sección'),
    (4, 'Mecánico'),
    (6, 'Calidad'),
    (7, 'Contabilidad')
ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre;

-- 2. Sincronización de secuencia de roles
SELECT setval('roles_id_seq', (SELECT COALESCE(MAX(id), 1) FROM roles));
