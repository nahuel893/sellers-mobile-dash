"""Seed script: load preventista → supervisor mapping into operations schema.

Reads data/supervisores.xlsx (34 rows, 2 cols without header: vendedor, supervisor)
and upserts all rows into operations.preventistas_supervisores in sellers_app_db.

Usage (from backend/):
    .venv/bin/python -m scripts.seed_supervisores

PostgreSQL connection uses APP_DB_* vars (sellers_app_db — App DB):
    APP_DB_HOST, APP_DB_PORT, APP_DB_NAME, APP_DB_USER, APP_DB_PASSWORD

The script is importable for testing (see tests/test_seed_supervisores.py).
The main entry-point is ``seed_supervisores()`` which can be called directly.
"""
from __future__ import annotations

import os
import pathlib
import sys

import psycopg2
from dotenv import load_dotenv

# Load .env from project root (3 levels above backend/scripts/seed_supervisores.py)
_env_path = pathlib.Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

# Default path — relative to project root
_XLSX_DEFAULT = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "supervisores.xlsx"


def _load_rows_from_xlsx(xlsx_path: pathlib.Path) -> list[tuple[str, str]]:
    """Read (vendedor, supervisor) pairs from xlsx. No header row.

    Returns:
        List of (preventista, supervisor) tuples — both stripped and uppercased.
    Raises:
        FileNotFoundError: if xlsx_path does not exist.
        ValueError: if the file has fewer than 1 data row or wrong column count.
    """
    import openpyxl

    if not xlsx_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {xlsx_path}")

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active

    rows: list[tuple[str, str]] = []
    for row in ws.iter_rows(values_only=True):
        if len(row) < 2:
            raise ValueError(
                f"Fila con menos de 2 columnas: {row}. "
                "El archivo debe tener columnas: vendedor, supervisor (sin encabezado)."
            )
        vendedor_val, supervisor_val = row[0], row[1]
        if vendedor_val is None or supervisor_val is None:
            continue  # skip empty rows
        rows.append((str(vendedor_val).strip(), str(supervisor_val).strip()))

    wb.close()

    if not rows:
        raise ValueError("El archivo no contiene filas de datos.")

    return rows


def seed_supervisores(xlsx_path: pathlib.Path | None = None) -> None:
    """Upsert preventista → supervisor mapping into operations schema (idempotent).

    Args:
        xlsx_path: path to supervisores.xlsx. Defaults to data/supervisores.xlsx
                   relative to the project root.
    Raises:
        FileNotFoundError: if the xlsx file is missing.
        SystemExit: on unrecoverable errors (missing file, DB unreachable).
    """
    if xlsx_path is None:
        xlsx_path = _XLSX_DEFAULT

    try:
        rows = _load_rows_from_xlsx(xlsx_path)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"ERROR al leer xlsx: {exc}", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(
        host=os.getenv("APP_DB_HOST", "localhost"),
        port=os.getenv("APP_DB_PORT", "5432"),
        dbname=os.getenv("APP_DB_NAME", "sellers_app_db"),
        user=os.getenv("APP_DB_USER"),
        password=os.getenv("APP_DB_PASSWORD"),
    )

    with conn.cursor() as cur:
        upserted = 0
        for preventista, supervisor in rows:
            cur.execute(
                """
                INSERT INTO operations.preventistas_supervisores (preventista, supervisor, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (preventista) DO UPDATE
                    SET supervisor  = EXCLUDED.supervisor,
                        updated_at  = NOW()
                """,
                (preventista, supervisor),
            )
            upserted += 1

    conn.commit()
    conn.close()
    print(f"Supervisores seeded: {upserted} rows upserted into operations.preventistas_supervisores.")


if __name__ == "__main__":
    seed_supervisores()
