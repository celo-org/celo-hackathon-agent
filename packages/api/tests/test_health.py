"""Tests for API health endpoints."""

from fastapi.testclient import TestClient


def test_api_imports():
    """Test that API module imports successfully."""
    from app.main import app

    assert app is not None


def test_health_endpoint():
    """Test health endpoint."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
