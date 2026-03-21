from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)

def test_create_database_instance():
    response = client.post(
        "/api/v1/database-instances/",
        json={
            "instance_label": "test-db-1",
            "host": "localhost",
            "port": 5432,
            "role": "PRIMARY",
            "priority": 1,
            "status": "ACTIVE"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["meta"]["request_id"]
    assert data["data"]["instance_label"] == "test-db-1"
    assert "id" in data["data"]

def test_read_database_instances():
    client.post(
        "/api/v1/database-instances/",
        json={
            "instance_label": "test-db-list",
            "host": "localhost",
            "port": 5432,
        },
    )
    response = client.get("/api/v1/database-instances/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0

def test_read_database_instance():
    # Create one first
    create_res = client.post(
        "/api/v1/database-instances/",
        json={
            "instance_label": "test-db-read",
            "host": "localhost",
            "port": 5432
        },
    )
    instance_id = create_res.json()["data"]["id"]
    
    response = client.get(f"/api/v1/database-instances/{instance_id}")
    assert response.status_code == 200
    assert response.json()["data"]["instance_label"] == "test-db-read"

def test_update_database_instance():
    create_res = client.post(
        "/api/v1/database-instances/",
        json={
            "instance_label": "test-db-update",
            "host": "localhost",
            "port": 5432
        },
    )
    instance_id = create_res.json()["data"]["id"]
    
    response = client.put(
        f"/api/v1/database-instances/{instance_id}",
        json={"instance_label": "updated-label"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["instance_label"] == "updated-label"

def test_delete_database_instance():
    create_res = client.post(
        "/api/v1/database-instances/",
        json={
            "instance_label": "test-db-delete",
            "host": "localhost",
            "port": 5432
        },
    )
    instance_id = create_res.json()["data"]["id"]
    
    response = client.delete(f"/api/v1/database-instances/{instance_id}")
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Database instance deleted"
    
    get_res = client.get(f"/api/v1/database-instances/{instance_id}")
    assert get_res.status_code == 404


def test_create_database_instance_requires_editor_role_in_header_mode(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_HEADER_EMAIL", "X-User-Email")
    monkeypatch.setattr(settings, "AUTH_HEADER_ROLE", "X-User-Role")

    response = client.post(
        "/api/v1/database-instances/",
        json={
            "instance_label": "auth-db-1",
            "host": "localhost",
            "port": 5432,
            "role": "PRIMARY",
            "priority": 1,
            "status": "ACTIVE"
        },
        headers={
            "X-User-Email": "viewer@example.com",
            "X-User-Role": "viewer",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to perform this action"


def test_create_database_instance_allows_editor_role_in_header_mode(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_HEADER_EMAIL", "X-User-Email")
    monkeypatch.setattr(settings, "AUTH_HEADER_ROLE", "X-User-Role")
    monkeypatch.setattr(settings, "AUTH_AUTO_PROVISION_USERS", True)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_EMAILS", "admin@example.com")

    create_user_response = client.post(
        "/api/v1/auth/users",
        json={
            "email": "editor@example.com",
            "display_name": "Editor",
            "role": "editor",
            "status": "ACTIVE",
        },
        headers={
            "X-User-Email": "admin@example.com",
        },
    )
    assert create_user_response.status_code == 201

    response = client.post(
        "/api/v1/database-instances/",
        json={
            "instance_label": "auth-db-2",
            "host": "localhost",
            "port": 5432,
            "role": "PRIMARY",
            "priority": 1,
            "status": "ACTIVE"
        },
        headers={
            "X-User-Email": "editor@example.com",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["instance_label"] == "auth-db-2"
