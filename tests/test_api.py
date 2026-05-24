from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_returns_200():
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_content_type_is_prometheus():
    response = client.get("/metrics")
    assert "text/plain" in response.headers["content-type"]
