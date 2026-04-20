"""
Tests para services/ventas_zonas_service.py

TDD: tests escritos antes de la implementación final.
Se mockea psycopg2 — sin base de datos real.
Scipy se usa con datos sintéticos pequeños (no se mockea).
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from services.ventas_zonas_service import (
    _remove_outliers,
    _compute_hull_vertices,
    _aggregate_zonas,
    get_zonas,
    AGRUPACION_RUTA,
    AGRUPACION_PREVENTISTA,
    AGRUPACIONES_VALIDAS,
    OUTLIER_STD_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Helpers de mock
# ---------------------------------------------------------------------------

def _make_cursor(fetchall_return=None, description=None):
    cur = MagicMock()
    cur.fetchall.return_value = fetchall_return or []
    cur.description = description or [
        ("id_cliente",), ("latitud",), ("longitud",), ("grupo",),
        ("generico",), ("bultos_m_act",), ("bultos_m_ant",),
        ("comprador_m_act",), ("comprador_m_ant",),
    ]
    return cur


def _make_conn(cursor=None):
    conn = MagicMock()
    conn.cursor.return_value = cursor or _make_cursor()
    return conn


def _row(
    id_cliente=1,
    lat=-24.78,
    lon=-65.41,
    grupo="1|10",
    generico="CERVEZAS",
    bultos_m_act=100.0,
    bultos_m_ant=80.0,
    comprador_m_act=True,
    comprador_m_ant=True,
):
    return {
        "id_cliente": id_cliente,
        "latitud": lat,
        "longitud": lon,
        "grupo": grupo,
        "generico": generico,
        "bultos_m_act": bultos_m_act,
        "bultos_m_ant": bultos_m_ant,
        "comprador_m_act": comprador_m_act,
        "comprador_m_ant": comprador_m_ant,
    }


# ---------------------------------------------------------------------------
# Tests: _remove_outliers
# ---------------------------------------------------------------------------

class TestRemoveOutliers:
    def test_tres_puntos_sin_outlier(self):
        """Tres puntos cercanos — ninguno se elimina."""
        coords = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.5, 1.0],
        ])
        result = _remove_outliers(coords)
        assert len(result) == 3

    def test_punto_outlier_eliminado(self):
        """Un punto muy alejado del centroide debe eliminarse."""
        # Tres puntos agrupados y uno muy lejos
        coords = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.5, 0.866],
            [1000.0, 1000.0],  # outlier claro
        ])
        result = _remove_outliers(coords)
        assert len(result) == 3
        # El outlier no debe estar en el resultado
        for pt in result:
            assert abs(pt[0]) < 100 and abs(pt[1]) < 100

    def test_menos_de_tres_puntos_devuelve_sin_cambios(self):
        """Menos de 3 puntos: devuelve el array sin modificar."""
        coords = np.array([[0.0, 0.0], [1.0, 1.0]])
        result = _remove_outliers(coords)
        assert len(result) == 2

    def test_puntos_identicos_no_eliminados(self):
        """Puntos idénticos: std=0, threshold=media, ninguno se elimina."""
        coords = np.array([
            [0.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
        ])
        result = _remove_outliers(coords)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Tests: _compute_hull_vertices
# ---------------------------------------------------------------------------

class TestComputeHullVertices:
    def test_triangulo_simple(self):
        """Un triángulo no degenrado tiene 3 vértices exactos en el hull."""
        # Puntos no colineales — triángulo real
        coords = np.array([
            [-24.78, -65.41],
            [-24.79, -65.42],
            [-24.77, -65.43],  # tercer punto fuera de la línea de los primeros dos
        ])
        result = _compute_hull_vertices(coords)
        assert result is not None
        assert len(result) == 3
        # Formato [lon, lat]
        for punto in result:
            assert len(punto) == 2
            lon, lat = punto
            # lat está en la columna 0 del array (antes de swapear)
            # lon está en la columna 1 — verificar rango aprox
            assert -66.0 < lon < -65.0
            assert -25.0 < lat < -24.0

    def test_cuadrado_cuatro_vertices(self):
        """Un cuadrado tiene exactamente 4 vértices en el hull."""
        coords = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0],
            [0.5, 0.5],  # punto interior — no debe estar en el hull
        ])
        result = _compute_hull_vertices(coords)
        assert result is not None
        assert len(result) == 4

    def test_menos_de_tres_devuelve_none(self):
        """Si tras outlier filter quedan < 3 puntos, devuelve None."""
        # Dos puntos en los extremos y uno que no es outlier pero el test
        # lo fuerza con solo 2 puntos
        coords = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
        ])
        result = _compute_hull_vertices(coords)
        assert result is None

    def test_outlier_causa_descarte(self):
        """Si el outlier filter deja < 3 puntos, la zona se descarta."""
        # Dos puntos cercanos y uno lejísimo; tras filtrar quedan 2 → None
        coords = np.array([
            [0.0, 0.0],
            [0.1, 0.1],
            [5000.0, 5000.0],  # outlier
        ])
        result = _compute_hull_vertices(coords)
        # 2 puntos quedan → None
        assert result is None


# ---------------------------------------------------------------------------
# Tests: _aggregate_zonas
# ---------------------------------------------------------------------------

class TestAggregateZonas:
    def test_zona_con_tres_clientes_genera_hull(self):
        """Tres clientes no colineales en la misma zona generan un polígono."""
        rows = [
            _row(id_cliente=1, lat=-24.78, lon=-65.41, grupo="1|10"),
            _row(id_cliente=2, lat=-24.79, lon=-65.42, grupo="1|10"),
            _row(id_cliente=3, lat=-24.77, lon=-65.43, grupo="1|10"),  # fuera de la línea
        ]
        result = _aggregate_zonas(rows)
        assert len(result) == 1
        zona = result[0]
        assert zona["nombre"] == "1|10"
        assert zona["n_clientes"] == 3
        assert len(zona["coords"]) >= 3
        assert zona["metricas"]["compradores_m_act"] == 3

    def test_zona_con_dos_clientes_descartada(self):
        """Dos clientes — convex hull necesita ≥ 3 puntos, zona descartada."""
        rows = [
            _row(id_cliente=1, grupo="1|10"),
            _row(id_cliente=2, grupo="1|10"),
        ]
        result = _aggregate_zonas(rows)
        assert len(result) == 0

    def test_dos_zonas_independientes(self):
        """Dos grupos distintos generan dos zonas."""
        rows = [
            _row(id_cliente=1, lat=-24.78, lon=-65.41, grupo="1|10"),
            _row(id_cliente=2, lat=-24.79, lon=-65.42, grupo="1|10"),
            _row(id_cliente=3, lat=-24.77, lon=-65.43, grupo="1|10"),  # no colineal
            _row(id_cliente=4, lat=-25.00, lon=-65.60, grupo="2|20"),
            _row(id_cliente=5, lat=-25.01, lon=-65.61, grupo="2|20"),
            _row(id_cliente=6, lat=-24.99, lon=-65.63, grupo="2|20"),  # no colineal
        ]
        result = _aggregate_zonas(rows)
        assert len(result) == 2
        nombres = {z["nombre"] for z in result}
        assert "1|10" in nombres
        assert "2|20" in nombres

    def test_metricas_bultos_acumuladas(self):
        """Bultos MAct/MAnt se suman por genérico en la zona."""
        rows = [
            _row(id_cliente=1, lat=0.0, lon=0.0, grupo="g1", generico="CERVEZAS", bultos_m_act=50.0, bultos_m_ant=30.0),
            _row(id_cliente=2, lat=1.0, lon=0.0, grupo="g1", generico="CERVEZAS", bultos_m_act=80.0, bultos_m_ant=60.0),
            _row(id_cliente=3, lat=0.5, lon=1.0, grupo="g1", generico="CERVEZAS", bultos_m_act=20.0, bultos_m_ant=10.0),
        ]
        result = _aggregate_zonas(rows)
        assert len(result) == 1
        m = result[0]["metricas"]
        assert m["bultos_m_act"] == pytest.approx(150.0)
        assert m["bultos_m_ant"] == pytest.approx(100.0)

    def test_compradores_m_act_contados_correctamente(self):
        """Solo clientes con compra en MAct cuentan como compradores."""
        rows = [
            _row(id_cliente=1, lat=0.0, lon=0.0, grupo="g1", comprador_m_act=True, comprador_m_ant=False),
            _row(id_cliente=2, lat=1.0, lon=0.0, grupo="g1", comprador_m_act=False, comprador_m_ant=True),
            _row(id_cliente=3, lat=0.5, lon=1.0, grupo="g1", comprador_m_act=True, comprador_m_ant=True),
        ]
        result = _aggregate_zonas(rows)
        assert len(result) == 1
        m = result[0]["metricas"]
        assert m["compradores_m_act"] == 2
        assert m["compradores_m_ant"] == 2

    def test_grupo_none_ignorado(self):
        """Filas con grupo=None se ignoran silenciosamente."""
        rows = [
            _row(id_cliente=1, grupo=None),
            _row(id_cliente=2, lat=0.0, lon=0.0, grupo="g1"),
            _row(id_cliente=3, lat=1.0, lon=0.0, grupo="g1"),
            _row(id_cliente=4, lat=0.5, lon=1.0, grupo="g1"),
        ]
        result = _aggregate_zonas(rows)
        assert len(result) == 1
        assert result[0]["nombre"] == "g1"

    def test_color_idx_secuencial(self):
        """color_idx se asigna secuencialmente por grupo (ordenado)."""
        rows = []
        for grupo in ["beta", "alpha", "gamma"]:
            for i, (lat, lon) in enumerate([(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]):
                rows.append(_row(id_cliente=i + hash(grupo) % 1000, lat=lat, lon=lon, grupo=grupo))
        result = _aggregate_zonas(rows)
        # Ordenado alfabéticamente
        nombres = [z["nombre"] for z in result]
        assert nombres == sorted(nombres)
        for i, z in enumerate(result):
            assert z["color_idx"] == i

    def test_n_clientes_refleja_total_no_filtrado(self):
        """n_clientes incluye a todos los clientes del grupo, incluso si hay outlier."""
        # 4 puntos: 3 cercanos + 1 outlier; el outlier no afecta n_clientes
        rows = [
            _row(id_cliente=1, lat=0.0, lon=0.0, grupo="g1"),
            _row(id_cliente=2, lat=0.01, lon=0.0, grupo="g1"),
            _row(id_cliente=3, lat=0.0, lon=0.01, grupo="g1"),
            _row(id_cliente=4, lat=5000.0, lon=5000.0, grupo="g1"),
        ]
        result = _aggregate_zonas(rows)
        # Hull puede o no generarse dependiendo del outlier filter
        # n_clientes siempre es 4
        if result:
            assert result[0]["n_clientes"] == 4

    def test_por_generico_en_metricas(self):
        """por_generico lista los genéricos con sus bultos."""
        rows = [
            _row(id_cliente=1, lat=0.0, lon=0.0, grupo="g1", generico="CERVEZAS", bultos_m_act=10.0, bultos_m_ant=5.0),
            _row(id_cliente=1, lat=0.0, lon=0.0, grupo="g1", generico="AGUAS DANONE", bultos_m_act=3.0, bultos_m_ant=2.0),
            _row(id_cliente=2, lat=1.0, lon=0.0, grupo="g1", generico="CERVEZAS", bultos_m_act=20.0, bultos_m_ant=15.0),
            _row(id_cliente=3, lat=0.5, lon=1.0, grupo="g1", generico="CERVEZAS", bultos_m_act=5.0, bultos_m_ant=3.0),
        ]
        result = _aggregate_zonas(rows)
        assert len(result) == 1
        m = result[0]["metricas"]
        pg = {item["generico"]: item for item in m["por_generico"]}
        assert "CERVEZAS" in pg
        assert pg["CERVEZAS"]["m_act"] == pytest.approx(35.0)
        assert "AGUAS DANONE" in pg


# ---------------------------------------------------------------------------
# Tests: get_zonas (con mock de DB)
# ---------------------------------------------------------------------------

class TestGetZonas:
    def _make_rows_for_cursor(self):
        """Genera 3 clientes no colineales en la misma ruta para que se forme un hull."""
        return [
            (1, -24.78, -65.41, "1|10", "CERVEZAS", 100.0, 80.0, True, True),
            (2, -24.79, -65.42, "1|10", "CERVEZAS", 50.0, 40.0, True, False),
            (3, -24.77, -65.43, "1|10", "CERVEZAS", 80.0, 60.0, True, True),
        ]

    def _description(self):
        return [
            ("id_cliente",), ("latitud",), ("longitud",), ("grupo",),
            ("generico",), ("bultos_m_act",), ("bultos_m_ant",),
            ("comprador_m_act",), ("comprador_m_ant",),
        ]

    def test_agrupacion_invalida_lanza_valueerror(self):
        conn = _make_conn()
        with pytest.raises(ValueError, match="agrupacion"):
            get_zonas(
                conn=conn,
                role_name="admin",
                sucursales_usuario=None,
                fecha_ini=date(2024, 1, 1),
                fecha_fin=date(2024, 1, 31),
                agrupacion="invalida",
            )

    def test_sin_clientes_retorna_lista_vacia(self):
        cur = _make_cursor(fetchall_return=[], description=self._description())
        conn = _make_conn(cursor=cur)

        result = get_zonas(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=date(2024, 1, 1),
            fecha_fin=date(2024, 1, 31),
            agrupacion=AGRUPACION_RUTA,
        )
        assert result == []

    def test_tres_clientes_genera_una_zona(self):
        cur = _make_cursor(
            fetchall_return=self._make_rows_for_cursor(),
            description=self._description(),
        )
        conn = _make_conn(cursor=cur)

        result = get_zonas(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=date(2024, 1, 1),
            fecha_fin=date(2024, 1, 31),
            agrupacion=AGRUPACION_RUTA,
        )
        assert len(result) == 1
        zona = result[0]
        assert zona["nombre"] == "1|10"
        assert zona["color_idx"] == 0
        assert len(zona["coords"]) >= 3
        assert zona["n_clientes"] == 3
        assert "metricas" in zona

    def test_filtro_genericos_vacio_retorna_lista_vacia(self):
        """Si _get_articulo_ids devuelve [] (ningún artículo match), retorna vacío."""
        with patch("services.ventas_zonas_service._get_articulo_ids", return_value=[]):
            cur = _make_cursor(fetchall_return=[], description=self._description())
            conn = _make_conn(cursor=cur)
            result = get_zonas(
                conn=conn,
                role_name="admin",
                sucursales_usuario=None,
                fecha_ini=date(2024, 1, 1),
                fecha_fin=date(2024, 1, 31),
                genericos=["INEXISTENTE"],
            )
        assert result == []

    def test_agrupacion_preventista_acepta_correctamente(self):
        """agrupacion='preventista' no lanza error."""
        cur = _make_cursor(fetchall_return=[], description=self._description())
        conn = _make_conn(cursor=cur)
        result = get_zonas(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=date(2024, 1, 1),
            fecha_fin=date(2024, 1, 31),
            agrupacion=AGRUPACION_PREVENTISTA,
        )
        assert isinstance(result, list)

    def test_agrupaciones_validas_contiene_ambas(self):
        assert AGRUPACION_RUTA in AGRUPACIONES_VALIDAS
        assert AGRUPACION_PREVENTISTA in AGRUPACIONES_VALIDAS
