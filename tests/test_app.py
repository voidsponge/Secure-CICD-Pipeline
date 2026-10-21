import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_security_headers_present(client):
    headers = client.get("/health").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in headers["Content-Security-Policy"]
    assert "max-age=" in headers["Strict-Transport-Security"]


def test_create_and_get_note(client):
    resp = client.post("/notes", json={"title": "Hello", "body": "World"})
    assert resp.status_code == 201
    note_id = resp.get_json()["id"]

    resp = client.get(f"/notes/{note_id}")
    assert resp.status_code == 200
    assert resp.get_json() == {"id": note_id, "title": "Hello", "body": "World"}


def test_list_and_delete(client):
    client.post("/notes", json={"title": "a", "body": ""})
    client.post("/notes", json={"title": "b", "body": ""})
    assert len(client.get("/notes").get_json()) == 2

    assert client.delete("/notes/1").status_code == 204
    assert client.delete("/notes/1").status_code == 404
    assert len(client.get("/notes").get_json()) == 1


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {"title": 1, "body": "x"},
        {"title": "", "body": "x"},
        {"title": "x" * 121, "body": "x"},
        {"title": "x", "body": "x" * 5001},
    ],
)
def test_rejects_invalid_input(client, payload):
    resp = client.post("/notes", json=payload)
    assert resp.status_code == 400


def test_sql_injection_attempt_is_harmless(client):
    client.post("/notes", json={"title": "keep me", "body": ""})
    evil = "x'); DROP TABLE notes; --"
    resp = client.post("/notes", json={"title": evil, "body": ""})
    assert resp.status_code == 201
    titles = [n["title"] for n in client.get("/notes").get_json()]
    assert titles == ["keep me", evil]


def test_non_integer_id_is_rejected(client):
    assert client.get("/notes/1 OR 1=1").status_code == 404


def test_oversized_payload_rejected(client):
    resp = client.post("/notes", data="x" * 20_000, content_type="application/json")
    assert resp.status_code == 413
