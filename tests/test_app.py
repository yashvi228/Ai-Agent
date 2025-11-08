import json
from app import create_app


def make_client():
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="test")
    return app.test_client()


def test_index():
    client = make_client()
    r = client.get("/")
    assert r.status_code == 200
    assert b"DeepSeek Chat" in r.data


def test_chat_requires_message():
    client = make_client()
    r = client.post("/api/chat", json={})
    assert r.status_code == 400


def test_commit_and_reset():
    client = make_client()
    r = client.post("/api/commit", json={"content": "hello"})
    assert r.status_code == 200
    r = client.post("/api/reset")
    assert r.status_code == 200

