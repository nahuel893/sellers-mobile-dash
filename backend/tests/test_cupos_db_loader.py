"""Tests for cupos loading from DB (gold.fact_cupos).

Covers:
- query_cupos_mes: SQL query construction (via mock)
- _mapear_cupos_desagregado: category/group mapping logic
- _cargar_cupos_db: integration (mocked DB calls)
- _cargar_supervisores_app_db: supervisor mapping
- _load_dataframe fallback to mock on DB error
"""
from __future__ import annotations

import importlib
import sys
from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_loader():
    """Reload data.data_loader to get a fresh module (resets caches)."""
    for key in list(sys.modules.keys()):
        if 'data_loader' in key or 'data.data_loader' in key:
            del sys.modules[key]
    return importlib.import_module('data.data_loader')


def _sample_raw_cupos() -> pd.DataFrame:
    """Minimal raw cupos DataFrame as returned by query_cupos_mes."""
    return pd.DataFrame({
        'vendedor':   ['JUAN PEREZ', 'JUAN PEREZ', 'JUAN PEREZ', 'JUAN PEREZ'],
        'sucursal':   ['1 - CASA CENTRAL'] * 4,
        'grupo_marca':['CERVEZAS', 'SALTA', 'HEINEKEN', 'AGUAS DANONE'],
        'cupo':       [1000.0, 300.0, 200.0, 50.0],
    })


# ---------------------------------------------------------------------------
# _mapear_cupos_desagregado
# ---------------------------------------------------------------------------

class TestMapearCuposDesagregado:
    """Unit tests for the desagregado → (categoria, grupo_marca) mapping."""

    def test_cervezas_becomes_total_cervezas(self):
        """'CERVEZAS' desagregado must map to grupo_marca='TOTAL_CERVEZAS'."""
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor':    ['V1'],
            'sucursal':    ['1 - CASA CENTRAL'],
            'grupo_marca': ['CERVEZAS'],
            'cupo':        [1000.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)

        row = df_out.iloc[0]
        assert row['grupo_marca'] == 'TOTAL_CERVEZAS'
        assert row['categoria'] == 'CERVEZAS'

    def test_salta_maps_to_cervezas_category(self):
        """'SALTA' desagregado must map to categoria='CERVEZAS', grupo_marca='SALTA'."""
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor':    ['V1'],
            'sucursal':    ['1 - CASA CENTRAL'],
            'grupo_marca': ['SALTA'],
            'cupo':        [300.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)

        row = df_out.iloc[0]
        assert row['categoria'] == 'CERVEZAS'
        assert row['grupo_marca'] == 'SALTA'

    def test_heineken_maps_correctly(self):
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor': ['V1'], 'sucursal': ['1 - CASA CENTRAL'],
            'grupo_marca': ['HEINEKEN'], 'cupo': [200.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)
        assert df_out.iloc[0]['categoria'] == 'CERVEZAS'
        assert df_out.iloc[0]['grupo_marca'] == 'HEINEKEN'

    def test_imperial_maps_correctly(self):
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor': ['V1'], 'sucursal': ['1 - CASA CENTRAL'],
            'grupo_marca': ['IMPERIAL'], 'cupo': [200.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)
        assert df_out.iloc[0]['grupo_marca'] == 'IMPERIAL'

    def test_miller_maps_correctly(self):
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor': ['V1'], 'sucursal': ['1 - CASA CENTRAL'],
            'grupo_marca': ['MILLER'], 'cupo': [200.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)
        assert df_out.iloc[0]['grupo_marca'] == 'MILLER'

    def test_multicervezas_maps_correctly(self):
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor': ['V1'], 'sucursal': ['1 - CASA CENTRAL'],
            'grupo_marca': ['MULTICERVEZAS'], 'cupo': [100.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)
        assert df_out.iloc[0]['categoria'] == 'CERVEZAS'
        assert df_out.iloc[0]['grupo_marca'] == 'MULTICERVEZAS'

    def test_importadas_maps_correctly(self):
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor': ['V1'], 'sucursal': ['1 - CASA CENTRAL'],
            'grupo_marca': ['IMPORTADAS'], 'cupo': [80.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)
        assert df_out.iloc[0]['categoria'] == 'CERVEZAS'
        assert df_out.iloc[0]['grupo_marca'] == 'IMPORTADAS'

    def test_aguas_danone_has_none_grupo_marca(self):
        """'AGUAS DANONE' must map to categoria='AGUAS_DANONE' with None grupo_marca."""
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor':    ['V1'],
            'sucursal':    ['1 - CASA CENTRAL'],
            'grupo_marca': ['AGUAS DANONE'],
            'cupo':        [50.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)

        row = df_out.iloc[0]
        assert row['categoria'] == 'AGUAS_DANONE'
        assert row['grupo_marca'] is None

    def test_multiccu_has_none_grupo_marca(self):
        """'MULTICCU' must map to categoria='MULTICCU' with None grupo_marca."""
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor':    ['V1'],
            'sucursal':    ['1 - CASA CENTRAL'],
            'grupo_marca': ['MULTICCU'],
            'cupo':        [75.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)

        row = df_out.iloc[0]
        assert row['categoria'] == 'MULTICCU'
        assert row['grupo_marca'] is None

    def test_unknown_desagregado_is_dropped(self):
        """Unknown desagregado values must be silently dropped."""
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor':    ['V1', 'V2'],
            'sucursal':    ['1 - CASA CENTRAL'] * 2,
            'grupo_marca': ['SALTA', 'UNKNOWN_BRAND'],
            'cupo':        [300.0, 100.0],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)

        assert len(df_out) == 1
        assert df_out.iloc[0]['grupo_marca'] == 'SALTA'

    def test_cupo_converted_to_int(self):
        """cupo must be rounded and converted to integer."""
        loader = _reload_loader()
        df_in = pd.DataFrame({
            'vendedor':    ['V1'],
            'sucursal':    ['1 - CASA CENTRAL'],
            'grupo_marca': ['SALTA'],
            'cupo':        [300.7654321],
        })
        df_out = loader._mapear_cupos_desagregado(df_in)

        assert df_out.iloc[0]['cupo'] == 301
        assert df_out.dtypes['cupo'] in [int, 'int64', 'int32']

    def test_output_columns(self):
        """Output must have exactly: vendedor, sucursal, categoria, grupo_marca, cupo."""
        loader = _reload_loader()
        df_out = loader._mapear_cupos_desagregado(_sample_raw_cupos())
        assert set(df_out.columns) == {'vendedor', 'sucursal', 'categoria', 'grupo_marca', 'cupo'}


# ---------------------------------------------------------------------------
# _cargar_supervisores_app_db
# ---------------------------------------------------------------------------

class TestCargarSupervisoresAppDb:
    """Unit tests for loading supervisor mapping from app_db."""

    def test_returns_dict_of_preventista_to_supervisor(self):
        """Must return a dict mapping preventista → supervisor."""
        loader = _reload_loader()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            ('JUAN PEREZ', 'SUPERVISOR_A'),
            ('MARIA GARCIA', 'SUPERVISOR_B'),
        ]
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_ctx

        with (
            patch('data.app_db.get_connection', return_value=mock_conn),
            patch('data.app_db.release_connection'),
        ):
            result = loader._cargar_supervisores_app_db()

        assert result == {
            'JUAN PEREZ': 'SUPERVISOR_A',
            'MARIA GARCIA': 'SUPERVISOR_B',
        }

    def test_queries_correct_table(self):
        """Must query operations.preventistas_supervisores."""
        loader = _reload_loader()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_ctx

        with (
            patch('data.app_db.get_connection', return_value=mock_conn),
            patch('data.app_db.release_connection'),
        ):
            loader._cargar_supervisores_app_db()

        executed = mock_cur.execute.call_args[0][0]
        assert 'operations.preventistas_supervisores' in executed

    def test_releases_connection_on_success(self):
        """Connection must be returned to pool after successful query."""
        loader = _reload_loader()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_ctx

        with (
            patch('data.app_db.get_connection', return_value=mock_conn) as mock_get,
            patch('data.app_db.release_connection') as mock_release,
        ):
            loader._cargar_supervisores_app_db()

        mock_release.assert_called_once_with(mock_conn)

    def test_releases_connection_on_error(self):
        """Connection must be returned to pool even if cursor raises."""
        loader = _reload_loader()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.execute.side_effect = RuntimeError("DB error")
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_ctx

        with (
            patch('data.app_db.get_connection', return_value=mock_conn),
            patch('data.app_db.release_connection') as mock_release,
        ):
            with pytest.raises(RuntimeError):
                loader._cargar_supervisores_app_db()

        mock_release.assert_called_once_with(mock_conn)


# ---------------------------------------------------------------------------
# _cargar_cupos_db
# ---------------------------------------------------------------------------

class TestCargarCuposDb:
    """Unit tests for _cargar_cupos_db — full mocked integration."""

    def _make_gold_conn_mock(self, df_return):
        """Return a mock gold_db connection whose read_sql returns df_return."""
        conn = MagicMock()
        return conn

    def test_returns_dataframe_with_required_columns(self):
        """_cargar_cupos_db must return DataFrame with all required columns."""
        loader = _reload_loader()

        mock_conn = MagicMock()

        with (
            patch('data.gold_db.get_connection', return_value=mock_conn),
            patch('data.gold_db.release_connection'),
            patch('data.queries.query_cupos_mes', return_value=_sample_raw_cupos()),
            patch.object(loader, '_cargar_supervisores_app_db', return_value={
                'JUAN PEREZ': 'SUPERVISOR_X',
            }),
        ):
            result = loader._cargar_cupos_db()

        assert result is not None
        required_cols = {'vendedor', 'sucursal', 'supervisor', 'categoria', 'grupo_marca', 'cupo'}
        assert required_cols.issubset(set(result.columns)), (
            f"Missing columns: {required_cols - set(result.columns)}"
        )

    def test_returns_none_when_query_empty(self):
        """_cargar_cupos_db must return None when DW returns no rows."""
        loader = _reload_loader()

        mock_conn = MagicMock()
        empty_df = pd.DataFrame(columns=['vendedor', 'sucursal', 'grupo_marca', 'cupo'])

        with (
            patch('data.gold_db.get_connection', return_value=mock_conn),
            patch('data.gold_db.release_connection'),
            patch('data.queries.query_cupos_mes', return_value=empty_df),
        ):
            result = loader._cargar_cupos_db()

        assert result is None

    def test_supervisor_is_assigned_from_map(self):
        """Vendedor with a match in sup_map must get their supervisor assigned."""
        loader = _reload_loader()

        mock_conn = MagicMock()
        raw = pd.DataFrame({
            'vendedor':    ['JUAN PEREZ'],
            'sucursal':    ['1 - CASA CENTRAL'],
            'grupo_marca': ['SALTA'],
            'cupo':        [300.0],
        })

        with (
            patch('data.gold_db.get_connection', return_value=mock_conn),
            patch('data.gold_db.release_connection'),
            patch('data.queries.query_cupos_mes', return_value=raw),
            patch.object(loader, '_cargar_supervisores_app_db', return_value={
                'JUAN PEREZ': 'GFLORES',
            }),
        ):
            result = loader._cargar_cupos_db()

        assert result is not None
        assert result.iloc[0]['supervisor'] == 'GFLORES'

    def test_supervisor_fallback_to_sin_supervisor(self):
        """Vendedor with no match in sup_map must get 'SIN SUPERVISOR'."""
        loader = _reload_loader()

        mock_conn = MagicMock()
        raw = pd.DataFrame({
            'vendedor':    ['UNKNOWN VENDEDOR'],
            'sucursal':    ['1 - CASA CENTRAL'],
            'grupo_marca': ['SALTA'],
            'cupo':        [300.0],
        })

        with (
            patch('data.gold_db.get_connection', return_value=mock_conn),
            patch('data.gold_db.release_connection'),
            patch('data.queries.query_cupos_mes', return_value=raw),
            patch.object(loader, '_cargar_supervisores_app_db', return_value={}),
        ):
            result = loader._cargar_cupos_db()

        assert result is not None
        assert result.iloc[0]['supervisor'] == 'SIN SUPERVISOR'

    def test_supervisor_gracefully_degrades_on_app_db_error(self):
        """If app_db fails, cupos still loads with 'SIN SUPERVISOR' fallback."""
        loader = _reload_loader()

        mock_conn = MagicMock()
        raw = pd.DataFrame({
            'vendedor':    ['JUAN PEREZ'],
            'sucursal':    ['1 - CASA CENTRAL'],
            'grupo_marca': ['SALTA'],
            'cupo':        [300.0],
        })

        with (
            patch('data.gold_db.get_connection', return_value=mock_conn),
            patch('data.gold_db.release_connection'),
            patch('data.queries.query_cupos_mes', return_value=raw),
            patch.object(loader, '_cargar_supervisores_app_db', side_effect=RuntimeError("app_db down")),
        ):
            result = loader._cargar_cupos_db()

        assert result is not None
        assert result.iloc[0]['supervisor'] == 'SIN SUPERVISOR'

    def test_periodo_uses_current_month(self):
        """query_cupos_mes must be called with the current month as 'YYYY-MM'."""
        loader = _reload_loader()

        mock_conn = MagicMock()
        called_with_periodo = {}

        def capture_query(conn, periodo, id_sucursal=1):
            called_with_periodo['periodo'] = periodo
            return pd.DataFrame(columns=['vendedor', 'sucursal', 'grupo_marca', 'cupo'])

        with (
            patch('data.gold_db.get_connection', return_value=mock_conn),
            patch('data.gold_db.release_connection'),
            patch('data.queries.query_cupos_mes', side_effect=capture_query),
        ):
            loader._cargar_cupos_db()

        expected_periodo = date.today().strftime('%Y-%m')
        assert called_with_periodo.get('periodo') == expected_periodo

    def test_releases_gold_connection_on_success(self):
        """Gold DB connection must be returned to pool after successful query."""
        loader = _reload_loader()

        mock_conn = MagicMock()

        with (
            patch('data.gold_db.get_connection', return_value=mock_conn) as mock_get,
            patch('data.gold_db.release_connection') as mock_release,
            patch('data.queries.query_cupos_mes', return_value=pd.DataFrame(
                columns=['vendedor', 'sucursal', 'grupo_marca', 'cupo']
            )),
        ):
            loader._cargar_cupos_db()

        mock_release.assert_called_once_with(mock_conn)

    def test_releases_gold_connection_on_error(self):
        """Gold DB connection must be returned to pool even if query raises."""
        loader = _reload_loader()

        mock_conn = MagicMock()

        with (
            patch('data.gold_db.get_connection', return_value=mock_conn),
            patch('data.gold_db.release_connection') as mock_release,
            patch('data.queries.query_cupos_mes', side_effect=RuntimeError("gold db down")),
        ):
            with pytest.raises(RuntimeError):
                loader._cargar_cupos_db()

        mock_release.assert_called_once_with(mock_conn)


# ---------------------------------------------------------------------------
# _load_dataframe — fallback behavior
# ---------------------------------------------------------------------------

class TestLoadDataframeFallback:
    """Test that _load_dataframe falls back to mock on DB errors."""

    def test_falls_back_to_mock_on_db_error(self):
        """When DB raises a connection error, _load_dataframe returns mock data."""
        loader = _reload_loader()

        import psycopg2

        with (
            patch('data.gold_db.get_connection', side_effect=psycopg2.OperationalError("no db")),
        ):
            df = loader._load_dataframe()

        # Mock data must have the expected columns
        required = {'vendedor', 'supervisor', 'categoria', 'grupo_marca', 'ventas', 'cupo'}
        assert required.issubset(set(df.columns))
        assert len(df) > 0

    def test_falls_back_to_mock_when_ventas_empty(self):
        """When ventas query returns empty, _load_dataframe returns mock data."""
        loader = _reload_loader()

        empty_ventas = pd.DataFrame(
            columns=['vendedor', 'sucursal', 'generico', 'marca', 'ventas']
        )

        with patch.object(loader, '_cargar_ventas_db', return_value=empty_ventas):
            df = loader._load_dataframe()

        required = {'vendedor', 'supervisor', 'categoria', 'grupo_marca', 'ventas', 'cupo'}
        assert required.issubset(set(df.columns))
        assert len(df) > 0

    def test_reraises_unexpected_errors(self):
        """Programming errors (unexpected exceptions) must NOT be swallowed."""
        loader = _reload_loader()

        with (
            patch.object(loader, '_cargar_ventas_db', side_effect=AttributeError("bug!")),
        ):
            with pytest.raises(AttributeError):
                loader._load_dataframe()


# ---------------------------------------------------------------------------
# RF-SPECIAL-CASES: TOTAL_CERVEZAS row in final merged dataframe
# ---------------------------------------------------------------------------

class TestSpecialCasesInLoadDataframe:
    """Test that TOTAL_CERVEZAS rows are properly included after merge."""

    def _make_ventas_df(self):
        return pd.DataFrame({
            'vendedor':    ['JUAN PEREZ'],
            'sucursal':    ['1 - CASA CENTRAL'],
            'generico':    ['CERVEZAS'],
            'marca':       ['SALTA'],
            'ventas':      [500.0],
        })

    def _make_cupos_df_with_total(self):
        """Cupos DataFrame including TOTAL_CERVEZAS row."""
        return pd.DataFrame({
            'vendedor':    ['JUAN PEREZ', 'JUAN PEREZ'],
            'sucursal':    ['1 - CASA CENTRAL', '1 - CASA CENTRAL'],
            'supervisor':  ['GFLORES', 'GFLORES'],
            'categoria':   ['CERVEZAS', 'CERVEZAS'],
            'grupo_marca': ['SALTA', 'TOTAL_CERVEZAS'],
            'cupo':        [300, 1000],
        })

    def test_total_cervezas_row_in_final_df(self):
        """After merge, the TOTAL_CERVEZAS row must appear in the final DataFrame."""
        loader = _reload_loader()

        with (
            patch.object(loader, '_cargar_ventas_db', return_value=self._make_ventas_df()),
            patch.object(loader, '_cargar_cupos_db', return_value=self._make_cupos_df_with_total()),
        ):
            df = loader._load_dataframe()

        total_rows = df[df['grupo_marca'] == 'TOTAL_CERVEZAS']
        assert len(total_rows) == 1, (
            f"Expected 1 TOTAL_CERVEZAS row, got {len(total_rows)}"
        )

    def test_total_cervezas_cupo_matches_dw(self):
        """The TOTAL_CERVEZAS cupo must be the one from DW, not summed from brands."""
        loader = _reload_loader()

        with (
            patch.object(loader, '_cargar_ventas_db', return_value=self._make_ventas_df()),
            patch.object(loader, '_cargar_cupos_db', return_value=self._make_cupos_df_with_total()),
        ):
            df = loader._load_dataframe()

        total_row = df[df['grupo_marca'] == 'TOTAL_CERVEZAS'].iloc[0]
        assert total_row['cupo'] == 1000
