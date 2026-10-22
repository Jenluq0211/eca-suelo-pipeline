CREATE TABLE IF NOT EXISTS resultados_eca (
    id SERIAL PRIMARY KEY,
    muestra VARCHAR(50),
    parametro VARCHAR(100),
    resultado NUMERIC(12,2),
    valor_eca NUMERIC(12,2),
    estado VARCHAR(20),
    fecha_proceso TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kpi_cumplimiento (
    id SERIAL PRIMARY KEY,
    uso_suelo VARCHAR(50),
    total_registros INTEGER,
    cumplen INTEGER,
    exceden INTEGER,
    sin_eca INTEGER,
    porcentaje_cumplimiento NUMERIC(10,2),
    fecha_proceso TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);