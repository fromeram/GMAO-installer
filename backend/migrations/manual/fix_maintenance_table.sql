
DO $$
BEGIN
    BEGIN
        ALTER TABLE maintenances 
        ADD COLUMN assigned_user_id INTEGER REFERENCES users(id),
        ADD COLUMN assigned_role_id INTEGER REFERENCES roles(id),
        ADD COLUMN is_completed BOOLEAN DEFAULT false,
        ADD COLUMN frequency VARCHAR,
        ADD COLUMN notification_interval INTEGER,
        ADD COLUMN next_maintenance_date TIMESTAMP,
        ADD COLUMN last_maintenance_date TIMESTAMP;
    EXCEPTION
        WHEN duplicate_column THEN
            NULL;
    END;
END $$;
