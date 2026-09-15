from fastapi.testclient import TestClient

from backend.integration.ml_backend import PackageMLBackend
from backend.main import create_app
from tests.fakes import FakeMLBackend


def _missing_importer(_name: str):
    raise ModuleNotFoundError("test package is intentionally absent")


def test_health_reports_ml_unavailable_without_faking_success() -> None:
    backend = PackageMLBackend(importer=_missing_importer)
    client = TestClient(create_app(backend))

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["ml_backend"]["available"] is False


def test_unavailable_ml_endpoint_returns_503() -> None:
    backend = PackageMLBackend(importer=_missing_importer)
    client = TestClient(create_app(backend))

    response = client.get("/api/models")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "ml_backend_unavailable"


def test_routes_delegate_to_fake_backend() -> None:
    client = TestClient(create_app(FakeMLBackend()))

    assert client.get("/api/models").json()[0]["id"] == "logistic_regression"
    assert client.get("/api/datasets").json()[0]["id"] == "wdbc"

    response = client.post(
        "/api/experiments",
        json={
            "model": "logistic_regression",
            "variant": "optimized",
            "dataset": "wdbc",
            "params": {"learning_rate": 0.1},
            "test_size": 0.2,
            "random_state": 42,
        },
    )

    assert response.status_code == 200
    assert response.json()["metrics"] == {"accuracy": 0.9}
    assert response.json()["diagnostics"]["source"] == "test-double"


def test_experiment_request_is_strictly_validated() -> None:
    client = TestClient(create_app(FakeMLBackend()))

    response = client.post(
        "/api/experiments",
        json={
            "model": "logistic_regression",
            "variant": "invented",
            "dataset": "wdbc",
            "test_size": 1.2,
            "unexpected": True,
        },
    )

    assert response.status_code == 422
    locations = {tuple(item["loc"]) for item in response.json()["detail"]}
    assert ("body", "variant") in locations
    assert ("body", "test_size") in locations
    assert ("body", "unexpected") in locations
