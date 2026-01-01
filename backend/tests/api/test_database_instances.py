from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.api.endpoints.database_instances import get_db

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

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
    assert data["instance_label"] == "test-db-1"
    assert "id" in data

def test_read_database_instances():
    response = client.get("/api/v1/database-instances/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

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
    instance_id = create_res.json()["id"]
    
    response = client.get(f"/api/v1/database-instances/{instance_id}")
    assert response.status_code == 200
    assert response.json()["instance_label"] == "test-db-read"

def test_update_database_instance():
    create_res = client.post(
        "/api/v1/database-instances/",
        json={
            "instance_label": "test-db-update",
            "host": "localhost",
            "port": 5432
        },
    )
    instance_id = create_res.json()["id"]
    
    response = client.put(
        f"/api/v1/database-instances/{instance_id}",
        json={"instance_label": "updated-label"}
    )
    assert response.status_code == 200
    assert response.json()["instance_label"] == "updated-label"

def test_delete_database_instance():
    create_res = client.post(
        "/api/v1/database-instances/",
        json={
            "instance_label": "test-db-delete",
            "host": "localhost",
            "port": 5432
        },
    )
    instance_id = create_res.json()["id"]
    
    response = client.delete(f"/api/v1/database-instances/{instance_id}")
    assert response.status_code == 204
    
    get_res = client.get(f"/api/v1/database-instances/{instance_id}")
    assert get_res.status_code == 404
