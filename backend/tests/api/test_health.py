from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.api.endpoints import health as health_endpoints


client = TestClient(app)


class FakeCursor:
    def __init__(self, responses=None, raise_on_drop=False):
        self.responses = list(responses or [])
        self.raise_on_drop = raise_on_drop
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))
        if self.raise_on_drop and "pg_drop_replication_slot" in str(query):
            raise RuntimeError("replication slot \"slot_a\" is active for PID 42")

    def fetchone(self):
        if self.responses:
            return self.responses.pop(0)
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.autocommit = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def close(self):
        self.closed = True


def auth_headers():
    return {
        "X-User-Email": "admin@example.com",
        "X-User-Role": "platform_admin",
    }


def test_drop_slot_uses_parameterized_queries(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_AUTO_PROVISION_USERS", True)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_EMAILS", "admin@example.com")

    fake_cursor = FakeCursor(responses=[("slot_a", None)])
    fake_connection = FakeConnection(fake_cursor)
    monkeypatch.setattr(health_endpoints.MaintenanceService, "connect_system_db", classmethod(lambda cls: fake_connection))

    response = client.post(
        "/api/v1/health/drop-slot",
        json={"slot_name": "slot_a"},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert fake_connection.closed is True
    assert fake_cursor.executed[0] == (
        "SELECT slot_name, active_pid FROM pg_replication_slots WHERE slot_name = %s",
        ("slot_a",),
    )
    assert fake_cursor.executed[1] == (
        "SELECT pg_drop_replication_slot(%s)",
        ("slot_a",),
    )


def test_drop_slot_returns_conflict_for_active_slot(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_AUTO_PROVISION_USERS", True)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_EMAILS", "admin@example.com")

    fake_cursor = FakeCursor(responses=[("slot_a", 42)], raise_on_drop=True)
    fake_connection = FakeConnection(fake_cursor)
    monkeypatch.setattr(health_endpoints.MaintenanceService, "connect_system_db", classmethod(lambda cls: fake_connection))

    response = client.post(
        "/api/v1/health/drop-slot",
        json={"slot_name": "slot_a"},
        headers=auth_headers(),
    )

    assert response.status_code == 409
    assert "Use force=true" in response.json()["detail"]


def test_vacuum_table_uses_composed_identifier_query(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_AUTO_PROVISION_USERS", True)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_EMAILS", "admin@example.com")

    fake_cursor = FakeCursor(responses=[("widgets",)])
    fake_connection = FakeConnection(fake_cursor)
    monkeypatch.setattr(health_endpoints.MaintenanceService, "connect_system_db", classmethod(lambda cls: fake_connection))

    response = client.post(
        "/api/v1/health/vacuum-table",
        json={"schema": "public", "table": "widgets", "full": True},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert fake_cursor.executed[0] == (
        "SELECT tablename FROM pg_tables WHERE schemaname = %s AND tablename = %s",
        ("public", "widgets"),
    )
    assert str(fake_cursor.executed[1][0]) == 'Composed([SQL(\'VACUUM FULL \'), Identifier(\'public\'), SQL(\'.\'), Identifier(\'widgets\')])'
    assert fake_cursor.executed[1][1] is None


def test_vacuum_table_rejects_invalid_identifier(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "header")
    monkeypatch.setattr(settings, "AUTH_AUTO_PROVISION_USERS", True)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_EMAILS", "admin@example.com")

    response = client.post(
        "/api/v1/health/vacuum-table",
        json={"schema": "public;drop", "table": "widgets"},
        headers=auth_headers(),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid schema name"
