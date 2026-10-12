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
