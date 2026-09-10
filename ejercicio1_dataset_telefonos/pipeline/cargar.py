"""Carga un lote de teléfonos desde un CSV "fuente" hacia staging, valida,
y publica en telefonos_clientes (o rechazados) con historial SCD tipo 2.

Uso:
    python -m pipeline.cargar --csv data/fuente_ejemplo.csv --fuente crm --id-lote lote-001
"""
from __future__ import annotations

import argparse
import csv
import os
import uuid
from pathlib import Path

import psycopg2

from .normalizar import normalizar_telefono

SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def get_conn():
    dsn = os.environ.get("DATABASE_URL", "postgresql://tuya:tuya@localhost:5433/tuya")
    return psycopg2.connect(dsn)


def aplicar_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def cargar_staging(conn, csv_path: Path, fuente: str, id_lote: str) -> int:
    with open(csv_path, encoding="utf-8", newline="") as f, conn.cursor() as cur:
        reader = csv.DictReader(f)
        rows = [(r["identificacion"], r["telefono"], fuente, id_lote) for r in reader]
        cur.executemany(
            "INSERT INTO staging_telefonos (identificacion, telefono_raw, fuente, id_lote) "
            "VALUES (%s, %s, %s, %s)",
            rows,
        )
    conn.commit()
    return len(rows)


def validar_y_publicar(conn, id_lote: str) -> tuple[int, int]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT identificacion, telefono_raw, fuente FROM staging_telefonos WHERE id_lote = %s",
            (id_lote,),
        )
        filas = cur.fetchall()

    aceptados = rechazados = 0
    with conn.cursor() as cur:
        for identificacion, telefono_raw, fuente in filas:
            resultado = normalizar_telefono(telefono_raw)

            if not resultado.valido:
                cur.execute(
                    "INSERT INTO rechazados (identificacion, telefono_raw, fuente, motivo, id_lote) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (identificacion, telefono_raw, fuente, resultado.motivo_rechazo, id_lote),
                )
                rechazados += 1
                continue

            cur.execute(
                "SELECT telefono FROM telefonos_clientes WHERE identificacion = %s AND es_vigente",
                (identificacion,),
            )
            vigente = cur.fetchone()
            if vigente and vigente[0] == resultado.telefono_normalizado:
                continue  # sin cambios, no genera nueva versión

            cur.execute(
                "UPDATE telefonos_clientes SET es_vigente = FALSE, vigente_hasta = now() "
                "WHERE identificacion = %s AND es_vigente",
                (identificacion,),
            )
            cur.execute(
                "INSERT INTO telefonos_clientes (identificacion, telefono, fuente, id_lote) "
                "VALUES (%s, %s, %s, %s)",
                (identificacion, resultado.telefono_normalizado, fuente, id_lote),
            )
            aceptados += 1

    conn.commit()
    return aceptados, rechazados


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--fuente", required=True)
    parser.add_argument("--id-lote", default=str(uuid.uuid4()))
    args = parser.parse_args()

    conn = get_conn()
    try:
        aplicar_schema(conn)
        n_staging = cargar_staging(conn, Path(args.csv), args.fuente, args.id_lote)
        aceptados, rechazados = validar_y_publicar(conn, args.id_lote)
        print(
            f"Lote {args.id_lote}: {n_staging} filas en staging -> "
            f"{aceptados} publicadas, {rechazados} rechazadas."
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
