-- Migración 002: agregar correo electrónico a confirmaciones
--
-- Nota: se agrega como NULL para no romper datos existentes.
-- La aplicación valida que para nuevos registros sea obligatorio.

ALTER TABLE confirmacion_asistencia
  ADD COLUMN email VARCHAR(254) NULL COMMENT 'Correo electrónico del encuestado (normalizado a minúsculas)' AFTER nombre_completo,
  ADD INDEX idx_email (email);
