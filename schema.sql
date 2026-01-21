-- Schema para sistema de confirmación de asistencia
-- FES Aragón - Informe de Gestión 2025

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS confirmacion_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE confirmacion_db;

-- Tabla de eventos
CREATE TABLE IF NOT EXISTS evento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL COMMENT 'Identificador único del evento para URLs',
    titulo VARCHAR(255) NOT NULL COMMENT 'Título del evento',
    fecha_inicio DATETIME NULL COMMENT 'Fecha y hora de inicio del evento',
    fecha_fin DATETIME NULL COMMENT 'Fecha y hora de fin del evento',
    lugar VARCHAR(255) NULL COMMENT 'Lugar (legacy). Se recomienda usar ubicacion_*',

    -- Ubicación predefinida (requerida)
    ubicacion_key VARCHAR(50) NOT NULL COMMENT 'Identificador interno de ubicación predefinida',
    ubicacion_nombre VARCHAR(255) NOT NULL COMMENT 'Nombre de la ubicación predefinida',
    ubicacion_lat DECIMAL(10,8) NOT NULL COMMENT 'Latitud de la ubicación del evento',
    ubicacion_lng DECIMAL(11,8) NOT NULL COMMENT 'Longitud de la ubicación del evento',

    activo BOOLEAN DEFAULT 0 COMMENT 'Solo puede haber un evento activo a la vez',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_slug (slug),
    INDEX idx_activo (activo),
    INDEX idx_ubicacion_key (ubicacion_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de confirmaciones de asistencia
CREATE TABLE IF NOT EXISTS confirmacion_asistencia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_evento INT NOT NULL COMMENT 'Referencia al evento',
    dependencia VARCHAR(255) NOT NULL COMMENT 'Dependencia a la que pertenece',
    puesto VARCHAR(255) NOT NULL COMMENT 'Puesto que ocupa',
    grado VARCHAR(50) NOT NULL COMMENT 'Grado académico: Dr., Dra., Mtro., Mtra., Lic., Ing., Arq., Otro',
    nombre_completo VARCHAR(255) NOT NULL COMMENT 'Nombre completo sin incluir el grado',
    email VARCHAR(254) NULL COMMENT 'Correo electrónico del encuestado (normalizado a minúsculas)',
    trae_vehiculo BOOLEAN DEFAULT 0 COMMENT 'Indica si asistirá con vehículo',
    vehiculo_modelo VARCHAR(100) NULL COMMENT 'Modelo del vehículo',
    vehiculo_color VARCHAR(50) NULL COMMENT 'Color del vehículo',
    vehiculo_placas VARCHAR(20) NULL COMMENT 'Placas del vehículo (normalizadas a mayúsculas sin espacios)',
    ip VARCHAR(45) NULL COMMENT 'Dirección IP del registro',
    user_agent TEXT NULL COMMENT 'User Agent del navegador',
    confirmado_en TIMESTAMP NULL COMMENT 'Fecha y hora de la confirmación',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Clave foránea
    FOREIGN KEY (id_evento) REFERENCES evento(id) ON DELETE CASCADE,
    
    -- Índice compuesto para evitar duplicados
    UNIQUE KEY unique_confirmacion (id_evento, nombre_completo, dependencia),
    
    -- Índices para mejorar búsquedas
    INDEX idx_id_evento (id_evento),
    INDEX idx_nombre (nombre_completo),
    INDEX idx_confirmado_en (confirmado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar evento de ejemplo (opcional)
INSERT INTO evento (
    slug, titulo, fecha_inicio, fecha_fin,
    lugar,
    ubicacion_key, ubicacion_nombre, ubicacion_lat, ubicacion_lng,
    activo
) 
VALUES (
    'informe-gestion-2025',
    'Primer Informe de Gestión 2024 - 2028 FES Aragón',
    '2025-02-15 10:00:00',
    '2025-02-15 14:00:00',
    'Teatro Jose Vasconcelos FES Aragón',
    'teatro-jose-vasconcelos',
    'Teatro José Vasconcelos',
    19.47639643,
    -99.04633426,
    1
) ON DUPLICATE KEY UPDATE slug=slug;

-- Comentarios adicionales sobre el diseño:
-- 1. La restricción UNIQUE (id_evento, nombre_completo, dependencia) evita duplicados
-- 2. Las placas se normalizan antes de guardar (mayúsculas, sin espacios/guiones)
-- 3. Los campos de vehículo son NULL si trae_vehiculo = 0
-- 4. utf8mb4 permite almacenar cualquier carácter Unicode, incluidos emojis
-- 5. ON DELETE CASCADE elimina confirmaciones si se elimina el evento
