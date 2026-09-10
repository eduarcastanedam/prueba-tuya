-- Esquema para el ejercicio de "Rachas".
-- Motor objetivo: SQLite (compatible en su mayoría con PostgreSQL / MySQL,
-- ver notas de portabilidad al final de este archivo).

DROP TABLE IF EXISTS historia;
DROP TABLE IF EXISTS retiros;

-- Saldo de cada cliente por corte de mes.
CREATE TABLE historia (
    identificacion TEXT    NOT NULL,
    corte_mes       DATE    NOT NULL,   -- fecha de corte tal cual viene en el Excel (último día del mes reportado)
    saldo           INTEGER NOT NULL,
    PRIMARY KEY (identificacion, corte_mes)
);

-- Fecha de retiro de los clientes que se retiraron.
CREATE TABLE retiros (
    identificacion  TEXT NOT NULL PRIMARY KEY,
    fecha_retiro    DATE NOT NULL
);

CREATE INDEX idx_historia_identificacion ON historia (identificacion);
CREATE INDEX idx_historia_corte_mes      ON historia (corte_mes);

-- Notas de portabilidad:
-- * DATE se guarda como TEXT 'YYYY-MM-DD' (formato nativo de fechas en SQLite).
-- * En PostgreSQL / MySQL, DATE puede declararse igual sin cambios funcionales;
--   la lógica de rachas en query_rachas.sql usa funciones de fecha estándar
--   (date(), julianday()) que tienen equivalentes directos en ambos motores
--   (date_trunc/interval en PostgreSQL, DATE_ADD en MySQL).
