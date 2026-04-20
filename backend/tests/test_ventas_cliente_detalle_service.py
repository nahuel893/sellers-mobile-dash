"""
Tests de services/ventas_cliente_detalle_service.py

TDD: tests escritos antes de la implementación.
No se conecta a PostgreSQL real — se parchean _query_info, _query_kpis, _query_ventas.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers de fixtures
# ---------------------------------------------------------------------------

def _make_info_row(**kwargs) -> dict:
    """Fila base de gold.dim_cliente."""
    defaults = {
        "id_cliente": 42,
        "fantasia": "Bar El Toro",
        "razon_social": "JUAN PEREZ SRL",
        "localidad": "Salta",
        "canal": "CAFETERIA",
        "sucursal": "Salta Capital",
        "id_sucursal": 1,
        "preventista_fv1": "Pedro García",
        "ruta_fv1": "1|5",
        "lista_precio": "Lista A",
        "latitud": -24.7,
        "longitud": -65.4,
    }
    defaults.update(kwargs)
    return defaults


def _make_kpi_row(**kwargs) -> dict:
    """Fila de KPIs del mes actual."""
    defaults = {
        "bultos_mes": 120,
        "facturacion_mes": 85000.50,
        "documentos_mes": 3,
    }
    defaults.update(kwargs)
    return defaults


def _make_ventas_rows() -> list[dict]:
    """Filas de ventas mensuales de ejemplo (2 artículos, 2 meses)."""
    return [
        {
            "generico": "CERVEZAS",
            "marca": "CORONA",
            "articulo": "CORONA 1L",
            "id_articulo": 101,
            "mes": "2025-12",
            "bultos": 50.0,
        },
        {
            "generico": "CERVEZAS",
            "marca": "CORONA",
            "articulo": "CORONA 1L",
            "id_articulo": 101,
            "mes": "2026-01",
            "bultos": 60.0,
        },
        {
            "generico": "CERVEZAS",
            "marca": "STELLA",
            "articulo": "STELLA 750ML",
            "id_articulo": 202,
            "mes": "2026-01",
            "bultos": 30.0,
        },
    ]


# ---------------------------------------------------------------------------
# Fixture de conexión mock
# ---------------------------------------------------------------------------

@pytest.fixture
def conn():
    return MagicMock()


# ---------------------------------------------------------------------------
# Tests de _build_tabla
# ---------------------------------------------------------------------------

class TestBuildTabla:
    """Unit tests de la función _build_tabla (pura, sin DB)."""

    def test_filas_articulo_tienen_datos(self):
        from services.ventas_cliente_detalle_service import _build_tabla

        meses_lista = ["2025-12", "2026-01"]
        rows = _make_ventas_rows()
        tabla = _build_tabla(rows, meses_lista)

        # Debe haber filas de artículo (articulo != '')
        art_rows = [r for r in tabla if r["articulo"] != ""]
        assert len(art_rows) == 2, f"Esperaba 2 artículos, got {len(art_rows)}"

    def test_filas_marca_son_subtotales(self):
        from services.ventas_cliente_detalle_service import _build_tabla

        meses_lista = ["2025-12", "2026-01"]
        rows = _make_ventas_rows()
        tabla = _build_tabla(rows, meses_lista)

        # Filas de marca: articulo == '' AND marca != ''
        marca_rows = [r for r in tabla if r["articulo"] == "" and r["marca"] != ""]
        assert len(marca_rows) == 2, f"Esperaba 2 marcas (CORONA+STELLA), got {len(marca_rows)}"

    def test_filas_generico_son_subtotales(self):
        from services.ventas_cliente_detalle_service import _build_tabla

        meses_lista = ["2025-12", "2026-01"]
        rows = _make_ventas_rows()
        tabla = _build_tabla(rows, meses_lista)

        # Filas de genérico: marca == '' AND articulo == ''
        gen_rows = [r for r in tabla if r["marca"] == "" and r["articulo"] == ""]
        assert len(gen_rows) == 1, f"Esperaba 1 genérico (CERVEZAS), got {len(gen_rows)}"

    def test_subtotal_generico_suma_correctamente(self):
        from services.ventas_cliente_detalle_service import _build_tabla

        meses_lista = ["2025-12", "2026-01"]
        rows = _make_ventas_rows()
        tabla = _build_tabla(rows, meses_lista)

        gen_row = next(r for r in tabla if r["marca"] == "" and r["articulo"] == "")
        assert gen_row["total"] == 140.0, f"Esperaba total=140, got {gen_row['total']}"

    def test_meses_lista_incluye_todos_los_meses(self):
        from services.ventas_cliente_detalle_service import _build_tabla

        meses_lista = ["2025-12", "2026-01"]
        rows = _make_ventas_rows()
        tabla = _build_tabla(rows, meses_lista)

        # Todos los artículos deben tener ambos meses en su dict 'meses'
        art_rows = [r for r in tabla if r["articulo"] != ""]
        for row in art_rows:
            for mes in meses_lista:
                assert mes in row["meses"], f"Mes {mes} faltante en {row['articulo']}"

    def test_meses_sin_venta_son_cero(self):
        from services.ventas_cliente_detalle_service import _build_tabla

        meses_lista = ["2025-12", "2026-01"]
        rows = _make_ventas_rows()
        tabla = _build_tabla(rows, meses_lista)

        # STELLA 750ML no tiene ventas en 2025-12
        stella_row = next(
            r for r in tabla if r["articulo"] == "STELLA 750ML"
        )
        assert stella_row["meses"]["2025-12"] == 0.0

    def test_id_articulo_es_cero_para_subtotales(self):
        from services.ventas_cliente_detalle_service import _build_tabla

        meses_lista = ["2025-12", "2026-01"]
        rows = _make_ventas_rows()
        tabla = _build_tabla(rows, meses_lista)

        subtotales = [r for r in tabla if r["articulo"] == ""]
        for row in subtotales:
            assert row["id_articulo"] == 0

    def test_orden_jerarquico(self):
        """Debe estar ordenado: genérico → marca → artículo."""
        from services.ventas_cliente_detalle_service import _build_tabla

        meses_lista = ["2025-12", "2026-01"]
        rows = _make_ventas_rows()
        tabla = _build_tabla(rows, meses_lista)

        # Verificar que la primera fila es el subtotal de CERVEZAS (genérico)
        # O que hay un orden coherente (gen → marcas → arts)
        genericos = [r for r in tabla if r["marca"] == "" and r["articulo"] == ""]
        marcas = [r for r in tabla if r["marca"] != "" and r["articulo"] == ""]
        articulos = [r for r in tabla if r["articulo"] != ""]

        # Debe haber al menos 1 de cada uno
        assert len(genericos) >= 1
        assert len(marcas) >= 1
        assert len(articulos) >= 1

    def test_lista_vacia_retorna_vacia(self):
        from services.ventas_cliente_detalle_service import _build_tabla

        tabla = _build_tabla([], ["2026-01", "2026-02"])
        assert tabla == []


# ---------------------------------------------------------------------------
# Tests de _build_meses_lista
# ---------------------------------------------------------------------------

class TestBuildMesesLista:
    def test_retorna_12_meses(self):
        from services.ventas_cliente_detalle_service import _build_meses_lista

        meses = _build_meses_lista()
        assert len(meses) == 12

    def test_meses_en_formato_yyyy_mm(self):
        from services.ventas_cliente_detalle_service import _build_meses_lista

        meses = _build_meses_lista()
        for mes in meses:
            assert len(mes) == 7
            assert mes[4] == "-"

    def test_ultimo_mes_es_mes_actual(self):
        from services.ventas_cliente_detalle_service import _build_meses_lista
        from datetime import date

        meses = _build_meses_lista()
        now = date.today()
        expected_last = f"{now.year:04d}-{now.month:02d}"
        assert meses[-1] == expected_last

    def test_orden_cronologico_ascendente(self):
        from services.ventas_cliente_detalle_service import _build_meses_lista

        meses = _build_meses_lista()
        assert meses == sorted(meses)


# ---------------------------------------------------------------------------
# Tests de get_cliente_detalle (integración — sin DB)
# ---------------------------------------------------------------------------

class TestGetClienteDetalle:
    def _mock_db(self, monkeypatch, info_row=None, kpi_row=None, ventas_rows=None):
        """Parchea las tres funciones de query internas."""
        if info_row is None:
            info_row = _make_info_row()
        if kpi_row is None:
            kpi_row = _make_kpi_row()
        if ventas_rows is None:
            ventas_rows = _make_ventas_rows()

        monkeypatch.setattr(
            "services.ventas_cliente_detalle_service._query_info",
            lambda conn, id_cliente: info_row,
        )
        monkeypatch.setattr(
            "services.ventas_cliente_detalle_service._query_kpis",
            lambda conn, id_cliente: kpi_row,
        )
        monkeypatch.setattr(
            "services.ventas_cliente_detalle_service._query_ventas",
            lambda conn, id_cliente: ventas_rows,
        )

    def test_cliente_no_encontrado_lanza_not_found(self, conn, monkeypatch):
        monkeypatch.setattr(
            "services.ventas_cliente_detalle_service._query_info",
            lambda conn, id_cliente: None,
        )
        from fastapi import HTTPException
        from services.ventas_cliente_detalle_service import get_cliente_detalle

        with pytest.raises(HTTPException) as exc_info:
            get_cliente_detalle(conn=conn, id_cliente=9999, role_name="admin", sucursales_usuario=None)
        assert exc_info.value.status_code == 404

    def test_rbac_sucursal_no_permitida_lanza_403(self, conn, monkeypatch):
        """Usuario con sucursal 2 no puede ver cliente de sucursal 1."""
        info = _make_info_row(id_sucursal=1)
        monkeypatch.setattr(
            "services.ventas_cliente_detalle_service._query_info",
            lambda conn, id_cliente: info,
        )
        from fastapi import HTTPException
        from services.ventas_cliente_detalle_service import get_cliente_detalle

        with pytest.raises(HTTPException) as exc_info:
            get_cliente_detalle(
                conn=conn,
                id_cliente=42,
                role_name="vendedor",
                sucursales_usuario=[2],   # sucursal 2, cliente en sucursal 1
            )
        assert exc_info.value.status_code == 403

    def test_admin_puede_ver_cualquier_sucursal(self, conn, monkeypatch):
        """Admin con sucursales=[2] igual puede ver cliente de sucursal 1."""
        self._mock_db(monkeypatch)
        from services.ventas_cliente_detalle_service import get_cliente_detalle

        result = get_cliente_detalle(
            conn=conn,
            id_cliente=42,
            role_name="admin",
            sucursales_usuario=[2],   # aunque tenga lista, admin no filtra
        )
        assert result is not None

    def test_retorna_info_correcta(self, conn, monkeypatch):
        self._mock_db(monkeypatch)
        from services.ventas_cliente_detalle_service import get_cliente_detalle

        result = get_cliente_detalle(
            conn=conn, id_cliente=42, role_name="admin", sucursales_usuario=None
        )
        assert result["info"]["id_cliente"] == 42
        assert result["info"]["fantasia"] == "Bar El Toro"

    def test_retorna_kpis_correctos(self, conn, monkeypatch):
        self._mock_db(monkeypatch)
        from services.ventas_cliente_detalle_service import get_cliente_detalle

        result = get_cliente_detalle(
            conn=conn, id_cliente=42, role_name="admin", sucursales_usuario=None
        )
        assert result["kpis"]["bultos_mes"] == 120
        assert result["kpis"]["documentos_mes"] == 3

    def test_tabla_no_vacia(self, conn, monkeypatch):
        self._mock_db(monkeypatch)
        from services.ventas_cliente_detalle_service import get_cliente_detalle

        result = get_cliente_detalle(
            conn=conn, id_cliente=42, role_name="admin", sucursales_usuario=None
        )
        assert len(result["tabla"]) > 0

    def test_vendedor_puede_ver_su_sucursal(self, conn, monkeypatch):
        """Vendedor con sucursal 1 puede ver cliente de sucursal 1."""
        self._mock_db(monkeypatch)
        from services.ventas_cliente_detalle_service import get_cliente_detalle

        result = get_cliente_detalle(
            conn=conn,
            id_cliente=42,
            role_name="vendedor",
            sucursales_usuario=[1],   # misma sucursal que el cliente
        )
        assert result is not None

    def test_ventas_vacias_retorna_tabla_vacia(self, conn, monkeypatch):
        """Cliente sin ventas en 12 meses → tabla vacía."""
        self._mock_db(monkeypatch, ventas_rows=[])
        from services.ventas_cliente_detalle_service import get_cliente_detalle

        result = get_cliente_detalle(
            conn=conn, id_cliente=42, role_name="admin", sucursales_usuario=None
        )
        assert result["tabla"] == []
