from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_check_returns_ok():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "VertTrade"
    assert payload["environment"] == "development"
    assert payload["database"] == "ok"
    assert payload["packaged"] is False
    assert "VertTrade" in payload["data_dir"] or "data" in payload["data_dir"]
