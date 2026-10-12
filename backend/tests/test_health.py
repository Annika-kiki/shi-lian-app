import os
import tempfile
from types import SimpleNamespace

from fastapi.testclient import TestClient


if "DATABASE_URL" not in os.environ:
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    os.environ["DATABASE_URL"] = f"sqlite:///{temp_db.name}"

from backend.main import app


client = TestClient(app)


def test_health_checks_database():
    with TestClient(app):
        pass
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "healthy"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_sensitive_endpoint_rate_limit(monkeypatch):
    import backend.main as main_module

    main_module.rate_limit_buckets.clear()
    monkeypatch.setattr(main_module, "settings", SimpleNamespace(sensitive_rate_limit_per_minute=1))
    payload = {"ingredients": ["鸡蛋"], "meal_type": "早餐", "target_calories": 300}
    assert client.post("/api/recipes/generate", json=payload).status_code == 401
    response = client.post("/api/recipes/generate", json=payload)
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    main_module.rate_limit_buckets.clear()


def test_rejected_gateway_host_is_logged_without_tokens(caplog):
    from fastapi import FastAPI
    from backend.main import LoggedTrustedHostMiddleware
    isolated_app = FastAPI()
    isolated_app.add_middleware(LoggedTrustedHostMiddleware, allowed_hosts=["verified.example"])
    with TestClient(isolated_app) as isolated_client:
        with caplog.at_level("WARNING", logger="backend.hosts"):
            response = isolated_client.get("/health", headers={"Host": "gateway.internal:8001", "Authorization": "Bearer do-not-log-me"})
    assert response.status_code == 400
    assert "gateway.internal:8001" in caplog.text
    assert "do-not-log-me" not in caplog.text
