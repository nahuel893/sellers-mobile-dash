"""Tests for backend/scripts/seed_visitas.py

All tests mock the DB connection (psycopg2) and the Excel reader (openpyxl).
No real PostgreSQL or Excel file is required.

Follows the same patterns established in test_seed_admin.py:
- _reload_seed() to force fresh module imports with monkeypatched env vars
- _make_conn_mock() to build a psycopg2 mock with cursor context manager
- patch targets: 'scripts.seed_visitas.psycopg2.connect'
                 'scripts.seed_visitas.openpyxl'
"""
import datetime
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_seed():
    """Force-reload the module so each test gets a clean state."""
    mod_name = "scripts.seed_visitas"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    return importlib.import_module(mod_name)


def _make_cursor_mock(rowcount: int = 1):
    """Build a mock cursor supporting the context-manager protocol."""
    cur = MagicMock()
    cur.rowcount = rowcount
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=cur)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx, cur


def _make_conn_mock(rowcount: int = 1):
    """Build a psycopg2 connection mock with a cursor mock attached."""
    ctx, cur = _make_cursor_mock(rowcount=rowcount)
    conn = MagicMock()
    conn.cursor.return_value = ctx
    return conn, cur


def _make_openpyxl_mock(rows: list[tuple]):
    """Build an openpyxl mock returning the given rows from ws.iter_rows.

    rows[0] is treated as the header row; rows[1:] are data rows.
    iter_rows is called twice: once for the header, once for data.
    We use side_effect to return the correct rows each call.
    """
    ws = MagicMock()

    # Header row (first call to iter_rows)
    header = [
        None, 'Id cliente', 'Id cliente erp', 'Descripción cliente',
        'Id ruta', 'Ruta', 'Domicilio', 'Sector', 'Fecha', 'Visitado',
        'Hora visita', 'Hora venta', 'Hora motivo', 'Motivo',
        'Latitud', 'Longitud', 'f/h foto',
    ]

    # iter_rows returns an iterator; we use side_effect on consecutive calls.
    call_count = [0]

    def iter_rows_side_effect(**kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            # Header request (min_row=1, max_row=1)
            yield tuple(header)
        else:
            # Data rows request (min_row=2)
            yield from rows

    ws.iter_rows = iter_rows_side_effect

    wb = MagicMock()
    wb.active = ws
    wb.close = MagicMock()

    openpyxl_mock = MagicMock()
    openpyxl_mock.load_workbook.return_value = wb

    return openpyxl_mock, wb, ws


def _sample_row(
    id_cliente=12345,
    id_ruta=8,
    ruta='GONZALEZ INES LU-JU',
    fecha='16-04-2026',
    visitado='SI',
    hora_visita='13:09:57',
    hora_venta=None,
    hora_motivo=None,
    motivo=None,
    latitud=-24.788,
    longitud=-65.408,
    domicilio='AVENIDA CONTRERAS 2051',
    sector='GONZALEZ INES',
    descripcion_cliente='CONSUMIDOR FINAL',
    foto_url=None,
):
    """Build a valid raw Excel row tuple."""
    return (
        None,                    # col 0 — ignored
        id_cliente,              # col 1 — Id cliente
        99999,                   # col 2 — Id cliente erp (ignored)
        descripcion_cliente,     # col 3 — Descripción cliente
        id_ruta,                 # col 4 — Id ruta
        ruta,                    # col 5 — Ruta
        domicilio,               # col 6 — Domicilio
        sector,                  # col 7 — Sector
        fecha,                   # col 8 — Fecha
        visitado,                # col 9 — Visitado
        hora_visita,             # col 10 — Hora visita
        hora_venta,              # col 11 — Hora venta
        hora_motivo,             # col 12 — Hora motivo
        motivo,                  # col 13 — Motivo
        latitud,                 # col 14 — Latitud
        longitud,                # col 15 — Longitud
        foto_url,                # col 16 — f/h foto
    )


# ---------------------------------------------------------------------------
# Tests: file not found
# ---------------------------------------------------------------------------

def test_seed_exits_if_xlsx_not_found(tmp_path):
    """Script must exit with code 1 if the xlsx file does not exist."""
    seed = _reload_seed()
    missing = str(tmp_path / "nonexistent.xlsx")
    with pytest.raises(SystemExit) as exc_info:
        seed.seed_visitas(missing)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Tests: parsing helpers (unit-level, no DB)
# ---------------------------------------------------------------------------

class TestParseDate:
    def test_string_dd_mm_yyyy(self):
        seed = _reload_seed()
        assert seed._parse_date("16-04-2026") == datetime.date(2026, 4, 16)

    def test_string_yyyy_mm_dd(self):
        seed = _reload_seed()
        assert seed._parse_date("2026-04-16") == datetime.date(2026, 4, 16)

    def test_datetime_object(self):
        seed = _reload_seed()
        dt = datetime.datetime(2026, 4, 16, 10, 30)
        assert seed._parse_date(dt) == datetime.date(2026, 4, 16)

    def test_date_object(self):
        seed = _reload_seed()
        d = datetime.date(2026, 4, 16)
        assert seed._parse_date(d) == d

    def test_none_returns_none(self):
        seed = _reload_seed()
        assert seed._parse_date(None) is None

    def test_empty_string_returns_none(self):
        seed = _reload_seed()
        assert seed._parse_date("") is None


class TestParseTime:
    def test_string_hhmmss(self):
        seed = _reload_seed()
        assert seed._parse_time("13:09:57") == datetime.time(13, 9, 57)

    def test_time_object(self):
        seed = _reload_seed()
        t = datetime.time(13, 9, 57)
        assert seed._parse_time(t) == t

    def test_none_returns_none(self):
        seed = _reload_seed()
        assert seed._parse_time(None) is None


class TestParseBool:
    def test_si_is_true(self):
        seed = _reload_seed()
        assert seed._parse_bool("SI") is True

    def test_no_is_false(self):
        seed = _reload_seed()
        assert seed._parse_bool("NO") is False

    def test_none_is_false(self):
        seed = _reload_seed()
        assert seed._parse_bool(None) is False


class TestParseFloat:
    def test_valid_float(self):
        seed = _reload_seed()
        assert seed._parse_float(-24.788) == pytest.approx(-24.788)

    def test_zero_returns_none(self):
        seed = _reload_seed()
        assert seed._parse_float(0) is None

    def test_none_returns_none(self):
        seed = _reload_seed()
        assert seed._parse_float(None) is None


# ---------------------------------------------------------------------------
# Tests: insert flow (mocked DB + mocked openpyxl)
# ---------------------------------------------------------------------------

def test_seed_inserts_valid_rows(tmp_path):
    """Valid rows must be inserted with the correct SQL and params."""
    # Create a dummy xlsx file so the path check passes
    xlsx = tmp_path / "visitados.xlsx"
    xlsx.write_bytes(b"")  # openpyxl is mocked, content doesn't matter

    row = _sample_row()
    openpyxl_mock, wb, ws = _make_openpyxl_mock([row])
    conn, cur = _make_conn_mock(rowcount=1)

    seed = _reload_seed()

    with patch("scripts.seed_visitas.openpyxl", openpyxl_mock):
        with patch("scripts.seed_visitas.psycopg2.connect", return_value=conn):
            result = seed.seed_visitas(str(xlsx))

    assert result["inserted"] == 1
    assert result["skipped"] == 0

    # Verify the INSERT SQL was called
    executed = [str(c.args[0]) for c in cur.execute.call_args_list if c.args]
    insert_calls = [s for s in executed if "INSERT" in s.upper() and "visitas_preventista" in s]
    assert insert_calls, f"Expected INSERT into visitas_preventista. Got: {executed}"

    # Verify ON CONFLICT clause is present
    assert all("ON CONFLICT" in s for s in insert_calls), (
        "INSERT must use ON CONFLICT for idempotency"
    )

    # Verify commit was called
    conn.commit.assert_called_once()


def test_seed_idempotent_second_run_inserts_zero(tmp_path):
    """When all rows already exist (rowcount=0), inserted count must be 0."""
    xlsx = tmp_path / "visitados.xlsx"
    xlsx.write_bytes(b"")

    row = _sample_row()
    openpyxl_mock, wb, ws = _make_openpyxl_mock([row])

    # rowcount=0 simulates ON CONFLICT DO NOTHING (no row inserted)
    conn, cur = _make_conn_mock(rowcount=0)

    seed = _reload_seed()

    with patch("scripts.seed_visitas.openpyxl", openpyxl_mock):
        with patch("scripts.seed_visitas.psycopg2.connect", return_value=conn):
            result = seed.seed_visitas(str(xlsx))

    assert result["inserted"] == 0
    assert result["skipped"] == 1  # skipped_conflict = 1


def test_seed_skips_rows_missing_id_cliente(tmp_path):
    """Rows without id_cliente must be skipped (not inserted)."""
    xlsx = tmp_path / "visitados.xlsx"
    xlsx.write_bytes(b"")

    # Row with None id_cliente
    bad_row = _sample_row(id_cliente=None)
    good_row = _sample_row(id_cliente=99999)
    openpyxl_mock, wb, ws = _make_openpyxl_mock([bad_row, good_row])
    conn, cur = _make_conn_mock(rowcount=1)

    seed = _reload_seed()

    with patch("scripts.seed_visitas.openpyxl", openpyxl_mock):
        with patch("scripts.seed_visitas.psycopg2.connect", return_value=conn):
            result = seed.seed_visitas(str(xlsx))

    # Only the good row should be inserted
    assert result["inserted"] == 1
    assert result["skipped"] == 1  # bad_row is in skipped_parse


def test_seed_skips_rows_missing_fecha(tmp_path):
    """Rows without fecha must be skipped (not inserted)."""
    xlsx = tmp_path / "visitados.xlsx"
    xlsx.write_bytes(b"")

    bad_row = _sample_row(fecha=None)
    openpyxl_mock, wb, ws = _make_openpyxl_mock([bad_row])
    conn, cur = _make_conn_mock(rowcount=1)

    seed = _reload_seed()

    with patch("scripts.seed_visitas.openpyxl", openpyxl_mock):
        with patch("scripts.seed_visitas.psycopg2.connect", return_value=conn):
            result = seed.seed_visitas(str(xlsx))

    assert result["inserted"] == 0


def test_seed_inserts_with_correct_params(tmp_path):
    """The params passed to cursor.execute must match the row data."""
    xlsx = tmp_path / "visitados.xlsx"
    xlsx.write_bytes(b"")

    row = _sample_row(
        id_cliente=12345,
        id_ruta=8,
        ruta='GONZALEZ INES LU-JU',
        fecha='16-04-2026',
        visitado='SI',
        hora_visita='13:09:57',
        latitud=-24.788,
        longitud=-65.408,
    )
    openpyxl_mock, wb, ws = _make_openpyxl_mock([row])
    conn, cur = _make_conn_mock(rowcount=1)

    seed = _reload_seed()
    captured_params = []

    def capture_execute(sql, params=None):
        if params:
            captured_params.append(params)
        cur.rowcount = 1

    cur.execute.side_effect = capture_execute

    with patch("scripts.seed_visitas.openpyxl", openpyxl_mock):
        with patch("scripts.seed_visitas.psycopg2.connect", return_value=conn):
            seed.seed_visitas(str(xlsx))

    assert captured_params, "No params captured from cursor.execute"
    params = captured_params[0]

    assert params["id_cliente"] == 12345
    assert params["id_ruta"] == 8
    assert params["ruta"] == "GONZALEZ INES LU-JU"
    assert params["fecha"] == datetime.date(2026, 4, 16)
    assert params["visitado"] is True
    assert params["hora_visita"] == datetime.time(13, 9, 57)
    assert params["latitud"] == pytest.approx(-24.788)
    assert params["longitud"] == pytest.approx(-65.408)


def test_seed_multiple_rows_all_inserted(tmp_path):
    """Multiple valid rows must each generate one INSERT call."""
    xlsx = tmp_path / "visitados.xlsx"
    xlsx.write_bytes(b"")

    rows = [
        _sample_row(id_cliente=1001, hora_visita="09:00:00"),
        _sample_row(id_cliente=1002, hora_visita="10:00:00"),
        _sample_row(id_cliente=1003, hora_visita="11:00:00"),
    ]
    openpyxl_mock, wb, ws = _make_openpyxl_mock(rows)
    conn, cur = _make_conn_mock(rowcount=1)

    seed = _reload_seed()

    with patch("scripts.seed_visitas.openpyxl", openpyxl_mock):
        with patch("scripts.seed_visitas.psycopg2.connect", return_value=conn):
            result = seed.seed_visitas(str(xlsx))

    assert result["inserted"] == 3
    assert result["skipped"] == 0
    assert cur.execute.call_count == 3


def test_seed_uses_on_conflict_do_nothing(tmp_path):
    """INSERT must include ON CONFLICT (id_cliente, fecha, hora_visita) DO NOTHING."""
    xlsx = tmp_path / "visitados.xlsx"
    xlsx.write_bytes(b"")

    row = _sample_row()
    openpyxl_mock, wb, ws = _make_openpyxl_mock([row])
    conn, cur = _make_conn_mock(rowcount=1)

    seed = _reload_seed()
    sqls_executed = []

    def capture_sql(sql, params=None):
        sqls_executed.append(sql)
        cur.rowcount = 1

    cur.execute.side_effect = capture_sql

    with patch("scripts.seed_visitas.openpyxl", openpyxl_mock):
        with patch("scripts.seed_visitas.psycopg2.connect", return_value=conn):
            seed.seed_visitas(str(xlsx))

    insert_sqls = [s for s in sqls_executed if "INSERT" in s.upper()]
    assert insert_sqls, "No INSERT SQL found"
    assert all("DO NOTHING" in s.upper() for s in insert_sqls), (
        "INSERT must use ON CONFLICT ... DO NOTHING"
    )
