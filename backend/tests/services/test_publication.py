from uuid import uuid4

import pytest

from app.services.publication import PublicationService


class FakeClient:
    def __init__(self):
        self.calls = []

    def execute_raw(self, query, params=None, autocommit=False):
        self.calls.append((query, params, autocommit))
        return []


@pytest.fixture
def fake_instance_db(monkeypatch):
    class FakeDb:
        def get(self, _model, _instance_id):
            return object()

    monkeypatch.setattr("app.services.publication.DatabaseClient", lambda _instance: FakeClient())
    return FakeDb()


def test_create_publication_uses_safe_identifier_sql(fake_instance_db, monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr("app.services.publication.DatabaseClient", lambda _instance: fake_client)

    service = PublicationService(fake_instance_db)
    service.create_publication(uuid4(), "arcore_pub", False, ["public.orders", "events"])

    query, params, autocommit = fake_client.calls[0]
    assert autocommit is True
    assert params is None
    rendered = str(query)
    assert "CREATE PUBLICATION " in rendered
    assert "Identifier('arcore_pub')" in rendered
    assert "Identifier('public')" in rendered
    assert "Identifier('orders')" in rendered
    assert "Identifier('events')" in rendered


def test_drop_publication_uses_safe_identifier_sql(fake_instance_db, monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr("app.services.publication.DatabaseClient", lambda _instance: fake_client)

    service = PublicationService(fake_instance_db)
    service.drop_publication(uuid4(), "arcore_pub")

    query, params, autocommit = fake_client.calls[0]
    assert autocommit is True
    assert params is None
    rendered = str(query)
    assert "DROP PUBLICATION IF EXISTS " in rendered
    assert "Identifier('arcore_pub')" in rendered


def test_create_publication_rejects_invalid_table_reference(fake_instance_db):
    service = PublicationService(fake_instance_db)

    with pytest.raises(RuntimeError, match="Invalid table reference"):
        service.create_publication(uuid4(), "arcore_pub", False, ["a.b.c"])
