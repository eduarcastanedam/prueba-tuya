"""Ejecuta query_rachas.sql contra la base ya cargada.

Uso:
    python run_query.py --fecha-base 2024-12-31 --n 3 [--db db/rachas.db]
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

QUERY_PATH = Path(__file__).parent / "query_rachas.sql"


def run(db_path: Path, fecha_base: str, n: int) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            QUERY_PATH.read_text(encoding="utf-8"),
            {"fecha_base": fecha_base, "n": n},
        )
        return cur.fetchall()
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fecha-base", required=True, help="YYYY-MM-DD")
    parser.add_argument("--n", type=int, required=True, help="longitud mínima de racha")
    parser.add_argument("--db", default=str(Path(__file__).parent / "db" / "rachas.db"))
    args = parser.parse_args()

    rows = run(Path(args.db), args.fecha_base, args.n)
    print(f"{'identificacion':<20}{'racha':>6}  {'fecha_fin':<12}nivel")
    for row in rows:
        print(f"{row['identificacion']:<20}{row['racha']:>6}  {row['fecha_fin']:<12}{row['nivel']}")
    print(f"\nTotal clientes con racha >= {args.n}: {len(rows)}")
