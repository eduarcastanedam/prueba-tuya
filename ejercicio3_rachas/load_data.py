"""Carga Rachas.xlsx (hojas historia/retiros) en una base de datos SQLite.

Uso:
    python load_data.py [--excel ../Rachas.xlsx] [--db db/rachas.db]
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import openpyxl

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def read_sheet_rows(path: Path, sheet_name: str) -> list[tuple]:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    return rows[1:]  # descarta encabezado


def to_iso_date(value) -> str:
    return value.date().isoformat() if hasattr(value, "date") else value


def dedup_historia(rows: list[tuple]) -> list[tuple]:
    """Colapsa (identificacion, corte_mes) duplicados quedándose con el saldo
    mayor (criterio conservador: ver README, sección Calidad de datos)."""
    best: dict[tuple, int] = {}
    for ident, corte, saldo in rows:
        key = (ident, corte)
        if key not in best or saldo > best[key]:
            best[key] = saldo
    duplicated_keys = len(rows) - len(best)
    if duplicated_keys:
        print(f"Aviso: {duplicated_keys} fila(s) duplicada(s) (identificacion, corte_mes) colapsadas quedándose con el saldo mayor.")
    return [(ident, corte, saldo) for (ident, corte), saldo in best.items()]


def load(excel_path: Path, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

        raw_historia_rows = [
            (str(ident), to_iso_date(corte), int(saldo))
            for ident, corte, saldo in read_sheet_rows(excel_path, "historia")
        ]
        historia_rows = dedup_historia(raw_historia_rows)
        conn.executemany(
            "INSERT INTO historia (identificacion, corte_mes, saldo) VALUES (?, ?, ?)",
            historia_rows,
        )

        retiros_rows = [
            (str(ident), to_iso_date(fecha))
            for ident, fecha in read_sheet_rows(excel_path, "retiros")
        ]
        conn.executemany(
            "INSERT INTO retiros (identificacion, fecha_retiro) VALUES (?, ?)",
            retiros_rows,
        )

        conn.commit()
        print(f"Cargadas {len(historia_rows)} filas en historia, {len(retiros_rows)} en retiros -> {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--excel", default=str(Path(__file__).parent.parent / "Rachas.xlsx"))
    parser.add_argument("--db", default=str(Path(__file__).parent / "db" / "rachas.db"))
    args = parser.parse_args()
    load(Path(args.excel), Path(args.db))
