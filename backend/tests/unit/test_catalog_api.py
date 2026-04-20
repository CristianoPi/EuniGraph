from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from eunigraph.api.deps import get_db_session
from eunigraph.api.routers import organizations as organizations_router
from eunigraph.api.routers import publications as publications_router
from eunigraph.api.routers import researchers as researchers_router
from eunigraph.main import app


def _override_db_session() -> object:
    return object()


def test_publications_count_endpoint_returns_exact_count(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_count(session: object, filters: object) -> int:
        captured["session"] = session
        captured["filters"] = filters
        return 1234

    app.dependency_overrides[get_db_session] = _override_db_session
    monkeypatch.setattr(publications_router, "count_publications", fake_count)

    try:
        client = TestClient(app)
        response = client.get("/api/v1/publications/count?title=demo")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"count": 1234}
    assert captured["filters"].title == "demo"


def test_researchers_count_endpoint_returns_exact_count(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_count(session: object, filters: object) -> int:
        captured["session"] = session
        captured["filters"] = filters
        return 4321

    app.dependency_overrides[get_db_session] = _override_db_session
    monkeypatch.setattr(researchers_router, "count_researchers", fake_count)

    try:
        client = TestClient(app)
        response = client.get("/api/v1/researchers/count?name=ada")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"count": 4321}
    assert captured["filters"].name == "ada"


def test_organizations_count_endpoint_returns_exact_count(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_count(session: object, filters: object) -> int:
        captured["session"] = session
        captured["filters"] = filters
        return 321

    app.dependency_overrides[get_db_session] = _override_db_session
    monkeypatch.setattr(organizations_router, "count_organizations", fake_count)

    try:
        client = TestClient(app)
        response = client.get("/api/v1/organizations/count?name=eunice")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"count": 321}
    assert captured["filters"].name == "eunice"
