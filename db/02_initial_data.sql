-- ==============================================================================
-- GMAO SYSTEM - Datos Base del Sistema (Producción / Nuevas Instalaciones)
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

-- 3. Logros e Insignias Predeterminados (Gamificación)
INSERT INTO achievements (id, name, description, type, rarity, icon, points, condition_json, active) VALUES
    (1, '⚡ Rayo McQueen', 'Completa una orden en menos de 1 hora', 'SPEED', 'COMMON', '⚡', 25, '{"type": "fast_completion", "max_hours": 1}', true),
    (2, '🚀 Productivo', 'Completa 5 órdenes en un día', 'SPEED', 'RARE', '🚀', 75, '{"type": "orders_per_day", "target": 5}', true),
    (3, '🌟 Súper Productivo', 'Completa 10 órdenes en un día', 'SPEED', 'EPIC', '🌟', 150, '{"type": "orders_per_day", "target": 10}', true),
    (4, '🎯 Precisión', '10 órdenes consecutivas sin retrabajo', 'QUALITY', 'COMMON', '🎯', 50, '{"type": "no_rework_streak", "target": 10}', true),
    (5, '💎 Perfeccionista', '25 órdenes consecutivas sin retrabajo', 'QUALITY', 'RARE', '💎', 125, '{"type": "no_rework_streak", "target": 25}', true),
    (6, '🏆 Maestro Artesano', '50 órdenes consecutivas sin retrabajo', 'QUALITY', 'LEGENDARY', '🏆', 300, '{"type": "no_rework_streak", "target": 50}', true),
    (7, '📅 Constante', 'Trabaja 7 días consecutivos', 'CONSISTENCY', 'COMMON', '📅', 35, '{"type": "daily_streak", "target_days": 7}', true),
    (8, '🔥 En Llamas', 'Trabaja 30 días consecutivos', 'CONSISTENCY', 'EPIC', '🔥', 200, '{"type": "daily_streak", "target_days": 30}', true),
    (9, '🌙 Búho Nocturno', 'Completa 5 órdenes después de las 20:00', 'TEAMWORK', 'RARE', '🌙', 80, '{"type": "night_shift_orders", "target": 5, "after_hour": 20}', true),
    (10, '🚨 Héroe de Emergencia', 'Resuelve 3 emergencias en una semana', 'TEAMWORK', 'EPIC', '🚨', 150, '{"type": "emergency_orders", "target": 3, "timeframe_days": 7}', true),
    (11, '🔧 Mecánico Experto', 'Completa 100 órdenes correctivas', 'LEARNING', 'RARE', '🔧', 150, '{"type": "order_type_count", "work_type": "Correctivo", "target": 100}', true),
    (12, '🛡️ Guardián Preventivo', 'Completa 50 mantenimientos preventivos', 'LEARNING', 'RARE', '🛡️', 125, '{"type": "order_type_count", "work_type": "Preventivo", "target": 50}', true),
    (13, '🔧 Primera Reparación', 'Completa tu primera orden de trabajo', 'LEARNING', 'COMMON', '🔧', 10, '{"type": "order_count", "target": 1}', true),
    (14, '🛠️ Mecánico Experimentado', 'Completa 50 órdenes de trabajo', 'LEARNING', 'RARE', '🛠️', 100, '{"type": "order_count", "target": 50}', true),
    (15, '⭐ Centurión', 'Completa 100 órdenes de trabajo', 'LEARNING', 'EPIC', '⭐', 200, '{"type": "order_count", "target": 100}', true),
    (16, '🎓 Primer Paso', 'Completa tu primera orden de trabajo', 'LEARNING', 'COMMON', '🎓', 10, '{"type": "order_count", "target": 1}', true),
    (17, '⚙️ En Marcha', 'Completa 10 órdenes de trabajo', 'LEARNING', 'COMMON', '⚙️', 25, '{"type": "order_count", "target": 10}', true),
    (18, '🔧 Técnico Competente', 'Completa 50 órdenes de trabajo', 'LEARNING', 'RARE', '🔧', 75, '{"type": "order_count", "target": 50}', true),
    (19, '👨‍🔧 Experto', 'Completa 100 órdenes de trabajo', 'LEARNING', 'EPIC', '👨‍🔧', 150, '{"type": "order_count", "target": 100}', true),
    (20, '🌟 Leyenda de la Planta', 'Completa 1000 órdenes de trabajo', 'LEARNING', 'LEGENDARY', '🌟', 1000, '{"type": "order_count", "target": 1000}', true),
    (21, '🚀 Productivo', 'Completa 3 órdenes en un día', 'SPEED', 'COMMON', '🚀', 30, '{"type": "orders_per_day", "target": 3}', true),
    (22, '🌟 Muy Productivo', 'Completa 5 órdenes en un día', 'SPEED', 'RARE', '🌟', 60, '{"type": "orders_per_day", "target": 5}', true),
    (23, '💫 Súper Productivo', 'Completa 8 órdenes en un día', 'SPEED', 'EPIC', '💫', 120, '{"type": "orders_per_day", "target": 8}', true),
    (24, '🎯 Precisión', '10 órdenes sin rechazos ni retrabajos', 'QUALITY', 'COMMON', '🎯', 50, '{"type": "no_rework_streak", "target": 10}', true),
    (25, '💎 Perfeccionista', '25 órdenes sin rechazos ni retrabajos', 'QUALITY', 'RARE', '💎', 125, '{"type": "no_rework_streak", "target": 25}', true),
    (26, '🏆 Maestro Artesano', '50 órdenes consecutivas sin errores', 'QUALITY', 'LEGENDARY', '🏆', 300, '{"type": "no_rework_streak", "target": 50}', true),
    (27, '📅 Constante', 'Trabaja 7 días seguidos', 'CONSISTENCY', 'COMMON', '📅', 35, '{"type": "daily_streak", "target_days": 7}', true),
    (28, '💪 Resistente', 'Trabaja 14 días seguidos', 'CONSISTENCY', 'RARE', '💪', 80, '{"type": "daily_streak", "target_days": 14}', true),
    (29, '🔥 Incansable', 'Trabaja 21 días seguidos (turno completo)', 'CONSISTENCY', 'EPIC', '🔥', 200, '{"type": "daily_streak", "target_days": 21}', true),
    (30, '🤝 Colaborador', 'Ayuda en 10 órdenes de otros técnicos', 'TEAMWORK', 'COMMON', '🤝', 60, '{"type": "assistance_count", "target": 10}', true),
    (31, '🌙 Búho Nocturno', 'Completa 20 órdenes en turno de noche', 'TEAMWORK', 'RARE', '🌙', 80, '{"type": "night_shift_orders", "target": 20}', true)
ON CONFLICT (id) DO NOTHING;
SELECT setval('achievements_id_seq', (SELECT COALESCE(MAX(id), 1) FROM achievements));

-- 4. Códigos de Falla Estándar (FCR)
INSERT INTO failure_codes (id, code, description, active) VALUES
    (1, 'FUG-ACE', 'Fuga de aceite', true),
    (3, 'FUG-AGU', 'Fuga de Agua / Refrigerante', false),
    (4, 'FUG-AIR', 'Fuga de Aire Comprimido', true),
    (5, 'RUI-ANO', 'Ruido Anormal / Excesivo', true),
    (6, 'VIB-EXC', 'Vibración Excesiva', true),
    (7, 'ROT-COM', 'Componente Roto / Quebrado / Fisurado', true),
    (8, 'DES-EXC', 'Desgaste Excesivo / Prematuro', true),
    (9, 'ATA-MEC', 'Atasco / Bloqueo Mecánico', true),
    (10, 'DES-ALI', 'Desalineación', true),
    (11, 'FLO-COM', 'Componente Flojo / Suelto', true),
    (12, 'SOB-CAL', 'Sobrecalentamiento (Mecánico)', true),
    (13, 'NO-ARR', 'No Arranca / Fallo de Arranque', true),
    (14, 'PAR-INES', 'Parada Inesperada / Disparo Protección', true),
    (15, 'SOB-CON', 'Sobreconsumo / Sobrecarga Eléctrica', true),
    (16, 'FAL-SEN', 'Fallo de Sensor / Detector', true),
    (17, 'FAL-CON', 'Fallo de Controlador / PLC / HMI', false),
    (18, 'ERR-COM', 'Error de Comunicación (Red, Bus)', false),
    (19, 'COR-CIR', 'Cortocircuito', true),
    (20, 'FAL-MOT', 'Fallo de Motor Eléctrico', true),
    (21, 'PRE-BAJ', 'Presión Baja (Hidráulica/Neumática)', false),
    (22, 'PRE-ALT', 'Presión Alta (Hidráulica/Neumática)', false),
    (23, 'FLU-INS', 'Flujo Insuficiente / Nulo', false),
    (24, 'CIL-ERR', 'Fallo Cilindro (Hidráulico/Neumático)', true),
    (25, 'VAL-ERR', 'Fallo Válvula (Hidráulica/Neumática)', true),
    (26, 'TMP-HOR', 'Temperatura Horno Fuera Rango', false),
    (27, 'PRE-PRE', 'Presión Prensa Incorrecta', false),
    (28, 'ASP-DEF', 'Aspiración / Filtrado Deficiente (Polvo)', true),
    (29, 'DOS-ERR', 'Error Dosificación (Materias primas, esmalte)', false),
    (30, 'ESM-DEF', 'Defecto Esmaltado / Aplicación', false),
    (31, 'TRA-ERR', 'Error Transporte / Avance Cinta', false),
    (32, 'MOL-DAN', 'Molde Prensa Dañado / Desajustado', false),
    (33, 'NO-FUNCIONA', 'Maquina parada', true),
    (34, 'CAMB-FORM', 'Cambio de Formato', true),
    (35, 'PAR-EMERG', 'Parada de emergencia activada', true),
    (36, 'MICR-SEG', 'Micro de Seguridad Abierto (Puerta, Barrera...)', true),
    (37, 'ERR-MOV', 'Movimiento Incorrecto o Errático (sacudidas, no llega)', true),
    (38, 'VEL-ANOR', 'Velocidad Anormal (demasiado lenta o rápida)', true),
    (39, 'AZUL-DESPUN', 'Azulejo Roto o Dañado por la máquina', true),
    (40, 'OLOR-QUEMADO', 'Olor a quemado (eléctrico/mecánico)', true)
ON CONFLICT (id) DO NOTHING;
SELECT setval('failure_codes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM failure_codes));

-- 5. Códigos de Causa Estándar (FCR)
INSERT INTO cause_codes (id, code, description, active) VALUES
    (1, 'ERR-OPE', 'Error de Operación / Mal Uso', true),
    (2, 'FAL-LUB', 'Falta / Incorrecta Lubricación', true),
    (3, 'FAL-LIMPIEZA', 'Falta de Limpieza / Obstrucción/ Acumulación de polvo, suciedad o tiestos en la máquina', true),
    (4, 'AJU-INC', 'Ajuste Incorrecto / Desajuste', true),
    (5, 'MANT-INADEC', 'Mantenimiento Inadecuado / Omitido/Falta de limpieza o mantenimiento preventivo programado', true),
    (6, 'MNT-PRE', 'Fallo Durante Mantenimiento Preventivo', false),
    (7, 'INS-INC', 'Instalación Incorrecta', true),
    (8, 'DES-NOR', 'Desgaste Normal / Fin Vida Útil  natural de componente (correa, rodamiento, cadena)', true),
    (9, 'FAT-MAT', 'Fatiga de Material', true),
    (10, 'DEF-FAB', 'Defecto de Fabricación (Componente)', true),
    (11, 'CON-COR', 'Contaminación / Corrosión', true),
    (12, 'PIE-ERR', 'Pieza / Repuesto Incorrecto', true),
    (13, 'DIS-DEF', 'Diseño Deficiente / Inadecuado', false),
    (14, 'SOB-CAR', 'Sobrecarga Operacional', true),
    (15, 'IMP-EXT', 'Impacto / Daño Externo', true),
    (16, 'CON-AMB', 'Condición Ambiental Adversa (Temp, Humedad, Polvo)', true),
    (17, 'ERR-DIS', 'Error en Diseño / Especificación', false),
    (18, 'FAL-SUM', 'Fallo Suministro Eléctrico / Fluctuación', true),
    (19, 'MAL-CON', 'Mala Conexión / Cableado Defectuoso', true),
    (20, 'FAL-PRO', 'Fallo Protección Eléctrica (Fusible, Térmico,/Disyuntor/Guardamotor disparado)', true),
    (21, 'PERSONAL-DEF', 'Desconocimiento de la operación estándar de la máquina, Personal con falta de formación, despiste personal,  ', true),
    (22, 'CAMB-FORM', 'Cambio de Formato', true),
    (23, 'ERROR-MANIP', 'Error de manipulación en modo manual/automático', true),
    (24, 'PAR-EMERG', 'Parada de emergencia/seguridad pulsada por error', true),
    (25, 'IMPAC-EXTER', 'Impacto externo (golpe con carretilla, caída de azulejo)', true),
    (26, 'MANIP-DEFEC', 'Manipulación de ajustes por personal no autorizado', true),
    (27, 'FALL-SENS', 'Fallo de sensor (fotocélula, inductivo, final de carrera)', true),
    (28, 'FALL-CONT', 'Fallo de contactor, relé o variador de frecuencia', true),
    (29, 'CABL-SUEL', 'Cableado dañado, suelto o en cortocircuito', true),
    (30, 'SOBR-MOT', 'Sobrecarga de motor por atasco o sobreesfuerzo', true),
    (31, 'DES-MECAN', 'Desajuste mecánico (topes, guías, fotocélulas)', true),
    (32, 'ENG-MAQU', 'Atasco o enganche de pieza/tiesto en la máquina', true),
    (33, 'EJE-COL', 'Eje de motor/reductor agarrotado, gripado o "colado"', true),
    (34, 'REDUC-FUGA', 'Fuga de aceite o grasa en reductor/sistema', true),
    (35, 'ROT-COMPO-', 'Rotura de componente mecánico (soporte, eje, piñón...)', true),
    (36, 'COCODRILO', 'Cadena portacables rota o atascada', true),
    (37, 'RACOR-MANG', 'Fuga o rotura en manguera o racor neumático', true),
    (38, 'FALL-EV-PIST', 'Fallo de electroválvula o cilindro neumático', true),
    (39, 'ERR-PARAM', 'Parámetro de producción incorrecto o desconfigurado', true),
    (40, 'FALL-SOFTW', 'Fallo de software o programa (requiere reinicio)', true)
ON CONFLICT (id) DO NOTHING;
SELECT setval('cause_codes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM cause_codes));

-- 6. Códigos de Remedio / Acción Estándar (FCR)
INSERT INTO remedy_codes (id, code, description, active) VALUES
    (1, 'AJU-PAR', 'Ajustar / Regular /cambiar Parámetros en Pantalla', true),
    (2, 'REA-PRE', 'Reapretar Conexiones / Pernos', true),
    (3, 'LIM-COM', 'Limpiar Componente\n/Desatasco', true),
    (4, 'LUB-COM', 'Lubricar Componente', true),
    (5, 'INS-COM', 'Inspeccionar / Verificar Componente o Sistema', true),
    (6, 'REE-COM', 'Reemplazar Componente / Pieza', true),
    (7, 'REP-COMPON', 'Reparación de componente (soldar, enderezar...)', true),
    (8, 'REC-COM', 'Recalibrar Sensor / Instrumento', true),
    (9, 'REARME-PROTEC', 'Rearmar / Resetear Sistema o Protección / emergencia / variador', true),
    (10, 'MOD-COM', 'Modificar Componente / Sistema', true),
    (11, 'SOL-FUG', 'Solucionar Fuga', true),
    (12, 'FORM-OPERARIO', 'Formación / Instrucción al operario sobre el manejo /Explicación del funcionamiento de seguridades/sensores', true),
    (13, 'ESP-REP', 'Esperando Repuesto', true),
    (14, 'ANA-CAU', 'Análisis de Causa Pendiente', true),
    (15, 'SIN-ACC', 'Sin Acción Requerida / No se encontró fallo', true),
    (16, 'CAMB-FORM', 'Cambio de Formato', true),
    (17, 'AJU-COMP', 'Ajuste / Regulación de componente mecánico', true),
    (18, 'SUST-MOTOR', 'Sustitución de motor eléctrico', true),
    (19, 'SUST-REDUC', 'Sustitución de reductor', true),
    (20, 'SUST-CORREA', 'Sustitución de correa / banda transportadora', true),
    (21, 'SUST-RODAM', 'Sustitución de rodamiento / casquillo', true),
    (22, 'SUST-FOT-SENS-MICRO', 'Sustitución de sensor / fotocélula / final de carrera', true),
    (23, 'SUST-RACOR', 'Sustitución de manguera / racor neumático', true),
    (24, 'SUST-FUSI-GUARDAM', 'Sustitución de fusible / disyuntor / guardamotor', true),
    (25, 'SUST-CONT-VF', 'Sustitución de contactor / relé / variador', true),
    (26, 'SUST-EJE-MECAN', 'Sustitución de componente mecánico (eje, soporte...)', true),
    (27, 'REPA-CABLEA', 'Reparación de cableado eléctrico', true),
    (28, 'LIMP-AREA', 'Limpieza general de la máquina o zona afectada / retirada de piezas o tiestos', true),
    (29, 'REINI-PLC', 'Reinicio de PLC / HMI (apagar y encender)', true)
ON CONFLICT (id) DO NOTHING;
SELECT setval('remedy_codes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM remedy_codes));
