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
        "user_id": None,
        "email": "system@local",
        "role": "platform_admin",
        "auth_mode": "disabled",
    }


def test_auth_me_requires_headers_in_header_mode(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication email header is required"


def test_auth_me_reads_header_principal_and_provisions_user(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_HEADER_EMAIL", "X-User-Email")
    monkeypatch.setattr(settings, "AUTH_HEADER_ROLE", "X-User-Role")
    monkeypatch.setattr(settings, "AUTH_AUTO_PROVISION_USERS", True)
    monkeypatch.setattr(settings, "AUTH_DEFAULT_ROLE", "viewer")

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-User-Email": "architect@example.com",
            "X-User-Role": "admin",
        },
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["email"] == "architect@example.com"
    assert body["role"] == "viewer"
    assert body["auth_mode"] == "header"
    assert body["user_id"]


def test_auth_admin_check_enforces_roles(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_AUTO_PROVISION_USERS", True)

    response = client.get(
        "/api/v1/auth/admin-check",
        headers={
            "X-User-Email": "viewer@example.com",
            "X-User-Role": "viewer",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to perform this action"


def test_auth_users_admin_endpoints_use_persisted_roles(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_HEADER_EMAIL", "X-User-Email")
    monkeypatch.setattr(settings, "AUTH_HEADER_ROLE", "X-User-Role")
    monkeypatch.setattr(settings, "AUTH_AUTO_PROVISION_USERS", True)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_EMAILS", "admin@example.com")

    create_response = client.post(
        "/api/v1/auth/users",
        json={
            "email": "operator@example.com",
            "display_name": "Operator",
            "role": "operator",
            "status": "ACTIVE",
        },
        headers={
            "X-User-Email": "admin@example.com",
            "X-User-Role": "platform_admin",
        },
    )
    assert create_response.status_code == 201

    list_response = client.get(
        "/api/v1/auth/users",
        headers={
            "X-User-Email": "admin@example.com",
            "X-User-Role": "platform_admin",
        },
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 2


def test_audit_log_requires_admin_and_returns_entries(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_HEADER_EMAIL", "X-User-Email")
    monkeypatch.setattr(settings, "AUTH_AUTO_PROVISION_USERS", True)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_EMAILS", "admin@example.com")

    create_user = client.post(
        "/api/v1/auth/users",
        json={
            "email": "operator@example.com",
            "display_name": "Operator",
            "role": "operator",
            "status": "ACTIVE",
        },
        headers={"X-User-Email": "admin@example.com"},
    )
    assert create_user.status_code == 201

    unauthorized = client.get(
        "/api/v1/audit/",
        headers={"X-User-Email": "viewer@example.com"},
    )
    assert unauthorized.status_code == 403

    authorized = client.get(
        "/api/v1/audit/",
        headers={"X-User-Email": "admin@example.com"},
    )
    assert authorized.status_code == 200
    rows = authorized.json()["data"]
    assert any(row["action"] == "auth.user.create" for row in rows)


def test_core_reads_require_authenticated_user_in_header_mode(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")

    response = client.get("/api/v1/applications/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication email header is required"


def test_applications_list_supports_pagination_and_filters():
    client.post(
        "/api/v1/applications/",
        json={
            "name": "Billing Hub",
            "owner_team": "Finance",
            "description": "Billing workflows",
            "status": "ACTIVE",
        },
    )
    client.post(
        "/api/v1/applications/",
        json={
            "name": "Archive Portal",
            "owner_team": "Ops",
            "description": "Historical data",
            "status": "ARCHIVED",
        },
    )

    response = client.get("/api/v1/applications/", params={"q": "Billing", "status": "ACTIVE", "limit": 1, "offset": 0})

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["meta"]["limit"] == 1
    assert body["meta"]["offset"] == 0
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Billing Hub"


def test_databases_list_supports_pagination_and_filters():
    app_response = client.post(
        "/api/v1/applications/",
        json={
            "name": "Analytics",
            "owner_team": "Data",
            "status": "ACTIVE",
        },
    )
    application_id = app_response.json()["data"]["id"]

    client.post(
        "/api/v1/databases/",
        json={
            "application_id": application_id,
            "name": "Warehouse",
            "db_type": "POSTGRES",
            "environment": "PROD",
            "database_name": "warehouse_prod",
            "status": "ACTIVE",
        },
    )
    client.post(
        "/api/v1/databases/",
        json={
            "application_id": application_id,
            "name": "Warehouse Dev",
            "db_type": "POSTGRES",
            "environment": "DEV",
            "database_name": "warehouse_dev",
            "status": "DISABLED",
        },
    )

    response = client.get(
        "/api/v1/databases/",
        params={"q": "warehouse", "environment": "PROD", "status": "ACTIVE", "limit": 1, "offset": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["meta"]["limit"] == 1
    assert body["meta"]["offset"] == 0
    assert len(body["data"]) == 1
    assert body["data"][0]["database_name"] == "warehouse_prod"
