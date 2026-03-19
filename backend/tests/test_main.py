from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "arcore-syncbridge"}

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
