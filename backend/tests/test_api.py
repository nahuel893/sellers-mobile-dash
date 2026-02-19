"""Tests de endpoints API usando mock data."""
import pytest
from fastapi.testclient import TestClient

from main import app
from dependencies import get_df
from data.mock_data import get_mock_dataframe


@pytest.fixture(autouse=True)
def override_deps():
    """Usa mock data para todos los tests de API."""
    app.dependency_overrides[get_df] = get_mock_dataframe
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


# --- Health check ---

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# --- Filtros ---

def test_sucursales(client):
    r = client.get("/api/sucursales")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_supervisores(client):
    r = client.get("/api/supervisores", params={"sucursal": "1 - CASA CENTRAL"})
    assert r.status_code == 200
    data = r.json()
    assert "BADIE" in data
    assert "LOPEZ" in data


def test_vendedores(client):
    r = client.get("/api/vendedores", params={
        "supervisor": "BADIE",
        "sucursal": "1 - CASA CENTRAL",
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert "FACUNDO CACERES" in data


# --- Dashboard ---

def test_dashboard(client):
    r = client.get("/api/dashboard", params={
        "supervisor": "BADIE",
        "sucursal": "1 - CASA CENTRAL",
    })
    assert r.status_code == 200
    data = r.json()
    assert "sucursal" in data
    assert "supervisor" in data
    assert "vendedores" in data
    assert len(data["vendedores"]) >= 1
    # Verificar estructura de categorías
    v = data["vendedores"][0]
    assert "CERVEZAS" in v["categories"]
    assert "MULTICCU" in v["categories"]
    assert "AGUAS_DANONE" in v["categories"]
    cat = v["categories"]["CERVEZAS"]
    assert "resumen" in cat
    assert "datos" in cat


def test_dashboard_resumen_fields(client):
    r = client.get("/api/dashboard", params={
        "supervisor": "BADIE",
        "sucursal": "1 - CASA CENTRAL",
    })
    data = r.json()
    resumen = data["vendedores"][0]["categories"]["CERVEZAS"]["resumen"]
    assert "pct_tendencia" in resumen
    assert "ventas" in resumen
    assert "cupo" in resumen
    assert "falta" in resumen
    assert "tendencia" in resumen
    assert resumen["falta"] == resumen["cupo"] - resumen["ventas"]


# --- Vendedor detail ---

def test_vendedor_detail(client):
    r = client.get("/api/vendedor/FACUNDO-CACERES")
    assert r.status_code == 200
    data = r.json()
    assert data["nombre"] == "FACUNDO CACERES"
    assert "CERVEZAS" in data["categories"]
    resumen = data["categories"]["CERVEZAS"]["resumen"]
    assert resumen["falta"] == resumen["cupo"] - resumen["ventas"]


def test_vendedor_not_found(client):
    r = client.get("/api/vendedor/NO-EXISTE")
    assert r.status_code == 404


# --- Supervisor detail ---

def test_supervisor_detail(client):
    r = client.get("/api/supervisor/BADIE", params={"sucursal": "1"})
    assert r.status_code == 200
    data = r.json()
    assert data["nombre"] == "BADIE"
    assert len(data["vendedores"]) >= 1
    assert "CERVEZAS" in data["categories"]


def test_supervisor_not_found(client):
    r = client.get("/api/supervisor/NO-EXISTE")
    assert r.status_code == 404


# --- Sucursal detail ---

def test_sucursal_detail(client):
    r = client.get("/api/sucursal/1")
    assert r.status_code == 200
    data = r.json()
    assert "CASA CENTRAL" in data["sucursal"]
    assert "CERVEZAS" in data["categories"]
    assert len(data["supervisores"]) >= 1


def test_sucursal_not_found(client):
    r = client.get("/api/sucursal/999")
    assert r.status_code == 404


# --- Config ---

def test_dias_habiles(client):
    r = client.get("/api/config/dias-habiles")
    assert r.status_code == 200
    data = r.json()
    assert data["habiles"] > 0
    assert data["transcurridos"] > 0
    assert data["restantes"] > 0
    assert "fecha" in data
