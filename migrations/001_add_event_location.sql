-- Migración 001: agregar ubicación predefinida a eventos
--
-- Nota: para bases ya existentes, primero agregamos columnas NULL,
--       luego rellenamos con un valor por defecto, y finalmente forzamos NOT NULL.

ALTER TABLE evento
  ADD COLUMN ubicacion_key VARCHAR(50) NULL COMMENT 'Identificador interno de ubicación predefinida',
  ADD COLUMN ubicacion_nombre VARCHAR(255) NULL COMMENT 'Nombre de la ubicación predefinida',
  ADD COLUMN ubicacion_lat DECIMAL(10,8) NULL COMMENT 'Latitud de la ubicación del evento',
  ADD COLUMN ubicacion_lng DECIMAL(11,8) NULL COMMENT 'Longitud de la ubicación del evento';

-- Default seguro para eventos existentes: Teatro José Vasconcelos
UPDATE evento
SET
  ubicacion_key = COALESCE(ubicacion_key, 'teatro-jose-vasconcelos'),
  ubicacion_nombre = COALESCE(ubicacion_nombre, 'Teatro José Vasconcelos'),
  ubicacion_lat = COALESCE(ubicacion_lat, 19.47639643),
  ubicacion_lng = COALESCE(ubicacion_lng, -99.04633426),
  lugar = COALESCE(lugar, 'Teatro José Vasconcelos')
WHERE
  ubicacion_key IS NULL
  OR ubicacion_nombre IS NULL
  OR ubicacion_lat IS NULL
  OR ubicacion_lng IS NULL;

ALTER TABLE evento
  MODIFY COLUMN ubicacion_key VARCHAR(50) NOT NULL,
  MODIFY COLUMN ubicacion_nombre VARCHAR(255) NOT NULL,
  MODIFY COLUMN ubicacion_lat DECIMAL(10,8) NOT NULL,
  MODIFY COLUMN ubicacion_lng DECIMAL(11,8) NOT NULL,
  ADD INDEX idx_ubicacion_key (ubicacion_key);
