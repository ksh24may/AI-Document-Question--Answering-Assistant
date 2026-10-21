
import pytest
from bson import ObjectId
from unittest.mock import MagicMock, patch

from app import app
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.test_client() as test_client:
        yield test_client


@patch("auth.users")
def test_register_success(users_mock, client):
    users_mock.find_one.return_value = None
    users_mock.insert_one.return_value = MagicMock(
        inserted_id=ObjectId()
    )

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "TEST@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 201
    assert response.json["success"] is True
    inserted_user = users_mock.insert_one.call_args.args[0]
    assert inserted_user["email"] == "test@example.com"
    assert inserted_user["password_hash"] != "password123"


@patch("auth.users")
def test_register_rejects_short_password(users_mock, client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "short"
        }
    )

    assert response.status_code == 400
    users_mock.insert_one.assert_not_called()


@patch("auth.users")
def test_login_success(users_mock, client):
    user_id = ObjectId()
    users_mock.find_one.return_value = {
        "_id": user_id,
        "name": "Test User",
        "email": "test@example.com",
        "password_hash": generate_password_hash("password123")
    }

    response = client.post(
        "/api/auth/login",
        json={
            "email": "TEST@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    assert response.json["success"] is True

    with client.session_transaction() as session:
        assert session["user_id"] == str(user_id)


@patch("auth.users")
def test_login_rejects_wrong_password(users_mock, client):
    users_mock.find_one.return_value = {
        "_id": ObjectId(),
        "name": "Test User",
        "email": "test@example.com",
        "password_hash": generate_password_hash("correct-password")
    }

    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrong-password"
        }
    )

    assert response.status_code == 401


def test_current_user_requires_login(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


@patch("auth.users")
def test_current_user_returns_logged_in_user(users_mock, client):
    user_id = ObjectId()
    users_mock.find_one.return_value = {
        "_id": user_id,
        "name": "Test User",
        "email": "test@example.com"
    }

    with client.session_transaction() as session:
        session["user_id"] = str(user_id)

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json["user"]["email"] == "test@example.com"


def test_logout_clears_session(client):
    with client.session_transaction() as session:
        session["user_id"] = str(ObjectId())

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert "user_id" not in session
