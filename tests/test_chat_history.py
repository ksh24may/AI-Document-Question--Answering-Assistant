
import pytest
from bson import ObjectId
from unittest.mock import patch, MagicMock

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.test_client() as test_client:
        yield test_client


def test_conversations_requires_login(client):
    response = client.get("/api/conversations")
    assert response.status_code == 401


def test_create_conversation_requires_login(client):
    response = client.post("/api/conversations", json={})
    assert response.status_code == 401


def test_get_messages_requires_login(client):
    response = client.get(
        f"/api/conversations/{ObjectId()}/messages"
    )
    assert response.status_code == 401


def test_save_message_requires_login(client):
    response = client.post(
        f"/api/conversations/{ObjectId()}/messages",
        json={"role": "user", "content": "Hello"}
    )
    assert response.status_code == 401


@patch("chat_history.conversations")
def test_user_cannot_access_another_users_conversation(
    conversations_mock, client
):
    user_id = str(ObjectId())
    other_conversation_id = ObjectId()

    with client.session_transaction() as session:
        session["user_id"] = user_id

    conversations_mock.find_one.return_value = None

    response = client.get(
        f"/api/conversations/{other_conversation_id}/messages"
    )

    assert response.status_code in (403, 404)
