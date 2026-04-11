from __future__ import annotations

from fastapi.testclient import TestClient

from eunigraph.main import app


def test_healthcheck_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "backend"}
