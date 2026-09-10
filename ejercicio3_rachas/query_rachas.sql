-- Rachas de nivel de saldo por cliente, "parado" en :fecha_base, con racha
-- mínima :n meses consecutivos en el mismo nivel.
--
-- Parámetros (named params de sqlite3):
--   :fecha_base  -> fecha 'YYYY-MM-DD' (ej. corte de mes) desde la cual se evalúa
--   :n           -> longitud mínima de racha exigida

WITH params AS (
    SELECT date(:fecha_base) AS fecha_base, :n AS n
),

-- Cortes de mes realmente existentes en los datos, hasta la fecha_base.
-- Se usa el propio dato (en vez de asumir periodicidad perfecta) para ser
-- robustos ante meses faltantes en la fuente.
cortes AS (
    SELECT DISTINCT corte_mes
    FROM historia, params
    WHERE corte_mes <= params.fecha_base
),

-- Primera aparición de cada cliente, considerando solo datos hasta fecha_base.
primera_aparicion AS (
    SELECT identificacion, MIN(corte_mes) AS corte_mes
    FROM historia, params
    WHERE corte_mes <= params.fecha_base
    GROUP BY identificacion
),

-- Rango de vigencia por cliente: desde su primera aparición hasta
-- min(fecha_base, fecha_retiro). Después de fecha_retiro no se imputa N0
-- (regla del enunciado), por lo que el cliente simplemente deja de generar
-- meses en el calendario.
clientes_rango AS (
    SELECT
        pa.identificacion,
        pa.corte_mes AS primera_aparicion,
        CASE
            WHEN r.fecha_retiro IS NOT NULL AND r.fecha_retiro <= p.fecha_base
                THEN r.fecha_retiro
            ELSE p.fecha_base
        END AS fecha_limite
    FROM primera_aparicion pa
    CROSS JOIN params p
    LEFT JOIN retiros r ON r.identificacion = pa.identificacion
),

-- Un mes por cliente para cada corte existente entre su primera aparición
-- y su fecha límite (calendario completo, sin huecos).
calendario AS (
    SELECT cr.identificacion, co.corte_mes
    FROM clientes_rango cr
    JOIN cortes co
        ON co.corte_mes BETWEEN cr.primera_aparicion AND cr.fecha_limite
),

-- Saldo efectivo: el real si existe, o 0 (N0) si el cliente no reportó ese
-- mes pero seguía vigente. (historia ya llega deduplicada por
-- identificacion + corte_mes desde load_data.py, ver README).
saldo_efectivo AS (
    SELECT
        cal.identificacion,
        cal.corte_mes,
        COALESCE(h.saldo, 0) AS saldo
    FROM calendario cal
    LEFT JOIN historia h
        ON h.identificacion = cal.identificacion
       AND h.corte_mes = cal.corte_mes
),

niveles AS (
    SELECT
        identificacion,
        corte_mes,
        CASE
            WHEN saldo >= 5000000 THEN 'N4'
            WHEN saldo >= 3000000 THEN 'N3'
            WHEN saldo >= 1000000 THEN 'N2'
            WHEN saldo >=  300000 THEN 'N1'
            ELSE 'N0'
        END AS nivel
    FROM saldo_efectivo
),

-- Truco "gaps and islands": la diferencia entre dos numeraciones
-- consecutivas es constante mientras el nivel no cambie mes a mes, lo que
-- agrupa cada racha ininterrumpida en un mismo "grupo".
islas AS (
    SELECT
        identificacion,
        corte_mes,
        nivel,
        ROW_NUMBER() OVER (PARTITION BY identificacion ORDER BY corte_mes)
        - ROW_NUMBER() OVER (PARTITION BY identificacion, nivel ORDER BY corte_mes) AS grupo
    FROM niveles
),

rachas AS (
    SELECT
        identificacion,
        nivel,
        COUNT(*)        AS racha,
        MAX(corte_mes)  AS fecha_fin
    FROM islas
    GROUP BY identificacion, nivel, grupo
),

rachas_validas AS (
    SELECT r.identificacion, r.nivel, r.racha, r.fecha_fin
    FROM rachas r, params p
    WHERE r.racha >= p.n
),

-- Desempate: racha más larga primero; si persiste el empate, la de fecha_fin
-- más reciente (siempre <= fecha_base por construcción del calendario).
rankeadas AS (
    SELECT
        identificacion, racha, fecha_fin, nivel,
        ROW_NUMBER() OVER (
            PARTITION BY identificacion
            ORDER BY racha DESC, fecha_fin DESC
        ) AS rn
    FROM rachas_validas
)

SELECT identificacion, racha, fecha_fin, nivel
FROM rankeadas
WHERE rn = 1
ORDER BY identificacion;
