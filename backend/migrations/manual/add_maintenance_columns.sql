
-- Agregar las columnas necesarias
ALTER TABLE maintenances 
ADD COLUMN IF NOT EXISTS assigned_user_id INTEGER,
ADD COLUMN IF NOT EXISTS assigned_role_id INTEGER,
ADD COLUMN IF NOT EXISTS is_completed BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS frequency VARCHAR,
ADD COLUMN IF NOT EXISTS notification_interval INTEGER,
ADD COLUMN IF NOT EXISTS next_maintenance_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_maintenance_date TIMESTAMP;

-- Agregar las foreign keys
ALTER TABLE maintenances 
ADD CONSTRAINT fk_maintenance_user 
FOREIGN KEY (assigned_user_id) 
REFERENCES users(id);

ALTER TABLE maintenances 
ADD CONSTRAINT fk_maintenance_role 
FOREIGN KEY (assigned_role_id) 
REFERENCES roles(id);
