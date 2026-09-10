-- Esquema para el dataset confiable de teléfonos de clientes.
-- Motor: PostgreSQL.

CREATE TABLE IF NOT EXISTS staging_telefonos (
    id              SERIAL PRIMARY KEY,
    identificacion  TEXT        NOT NULL,
    telefono_raw    TEXT        NOT NULL,
    fuente          TEXT        NOT NULL,
    id_lote         TEXT        NOT NULL,
    cargado_en      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rechazados (
    id              SERIAL PRIMARY KEY,
    identificacion  TEXT        NOT NULL,
    telefono_raw    TEXT        NOT NULL,
    fuente          TEXT        NOT NULL,
    motivo          TEXT        NOT NULL,
    id_lote         TEXT        NOT NULL,
    rechazado_en    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Dataset confiable, con histórico (SCD tipo 2): cada cambio de teléfono
-- cierra la fila vigente anterior en vez de sobrescribirla.
CREATE TABLE IF NOT EXISTS telefonos_clientes (
    id              SERIAL PRIMARY KEY,
    identificacion  TEXT        NOT NULL,
    telefono        TEXT        NOT NULL,
    fuente          TEXT        NOT NULL,
    id_lote         TEXT        NOT NULL,
    vigente_desde   TIMESTAMPTZ NOT NULL DEFAULT now(),
    vigente_hasta   TIMESTAMPTZ,
    es_vigente      BOOLEAN     NOT NULL DEFAULT TRUE
);

-- Un cliente solo puede tener un teléfono vigente a la vez.
CREATE UNIQUE INDEX IF NOT EXISTS ux_telefonos_clientes_vigente
    ON telefonos_clientes (identificacion)
    WHERE es_vigente;

CREATE INDEX IF NOT EXISTS idx_telefonos_clientes_identificacion
    ON telefonos_clientes (identificacion);
