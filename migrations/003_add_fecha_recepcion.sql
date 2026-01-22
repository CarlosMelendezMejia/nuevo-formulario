-- Agrega campo de fecha/hora de recepción al evento
ALTER TABLE evento
    ADD COLUMN fecha_recepcion DATETIME NULL COMMENT 'Fecha y hora de recepción'
    AFTER titulo;
