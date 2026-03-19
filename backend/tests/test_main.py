from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "arcore-syncbridge"}


def test_readiness_check():
    response = client.get("/ready")
    assert response.status_code in {200, 503}
    assert response.json()["service"] == "arcore-syncbridge"
    assert response.json()["status"] in {"ready", "not_ready"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_http_errors_use_structured_envelope():
    route_path = "/__test/http-error"

    async def raise_http_error():
        raise HTTPException(status_code=418, detail="teapot")

    app.add_api_route(route_path, raise_http_error, methods=["GET"])

    response = client.get(route_path)

    assert response.status_code == 418
    assert response.headers["x-request-id"]
    assert response.json() == {
        "error": {
            "code": "IM_A_TEAPOT",
            "message": "teapot",
            "request_id": response.headers["x-request-id"],
            "status_code": 418,
        },
        "detail": "teapot",
    }


def test_not_found_uses_structured_envelope():
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.headers["x-request-id"]
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Not Found",
            "request_id": response.headers["x-request-id"],
            "status_code": 404,
        },
        "detail": "Not Found",
    }


def test_unhandled_errors_use_structured_envelope():
    route_path = "/__test/runtime-error"

    async def raise_runtime_error():
        raise RuntimeError("boom")

    app.add_api_route(route_path, raise_runtime_error, methods=["GET"])

    error_client = TestClient(app, raise_server_exceptions=False)
    response = error_client.get(route_path)

    assert response.status_code == 500
    assert response.headers["x-request-id"]
    assert response.json() == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error",
            "request_id": response.headers["x-request-id"],
            "status_code": 500,
        },
        "detail": "Internal server error",
    }


def test_auth_me_returns_disabled_mode_principal(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "disabled")
    monkeypatch.setattr(settings, "AUTH_DISABLED_ROLE", "platform_admin")

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {
        "email": "system@local",
        "role": "platform_admin",
        "auth_mode": "disabled",
    }


def test_auth_me_requires_headers_in_header_mode(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication headers are required"


def test_auth_me_reads_header_principal(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_HEADER_EMAIL", "X-User-Email")
    monkeypatch.setattr(settings, "AUTH_HEADER_ROLE", "X-User-Role")

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-User-Email": "architect@example.com",
            "X-User-Role": "admin",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "email": "architect@example.com",
        "role": "admin",
        "auth_mode": "header",
    }


def test_auth_admin_check_enforces_roles(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")

    response = client.get(
        "/api/v1/auth/admin-check",
        headers={
            "X-User-Email": "viewer@example.com",
            "X-User-Role": "viewer",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to perform this action"
