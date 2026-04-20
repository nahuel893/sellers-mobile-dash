"""Test that admin_router is registered in the main FastAPI app.

Verifies that /api/admin/* routes appear in the OpenAPI route list.
"""
from __future__ import annotations


def test_admin_router_routes_registered():
    """admin_router endpoints are present in the main app route table."""
    from main import app

    routes = {route.path for route in app.routes}

    assert "/api/admin/users" in routes
    assert "/api/admin/users/{user_id}" in routes
    assert "/api/admin/users/{user_id}/password" in routes
    assert "/api/admin/roles" in routes
    assert "/api/admin/sucursales" in routes


def test_admin_routes_require_admin_role():
    """Hitting /api/admin/users without a token returns 401 (not 404)."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/admin/users")
    # 401 means the route exists and the auth guard is active
    assert res.status_code == 401
