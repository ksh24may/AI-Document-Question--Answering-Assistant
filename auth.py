
from datetime import datetime, timezone
from functools import wraps

from bson import ObjectId
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

from database import users

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "error": "Please log in first."
            }), 401

        return function(*args, **kwargs)

    return wrapper


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")

    if not all(isinstance(value, str) for value in [name, email, password]):
        return jsonify({"success": False, "error": "Invalid input types."}), 400

    name = name.strip()
    email = email.strip().lower()

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "error": "Name, email and password are required."
        }), 400

    if len(password) < 8:
        return jsonify({
            "success": False,
            "error": "Password must contain at least 8 characters."
        }), 400

    if users.find_one({"email": email}):
        return jsonify({
            "success": False,
            "error": "An account with this email already exists."
        }), 409

    user = {
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.now(timezone.utc)
    }

    result = users.insert_one(user)

    return jsonify({
        "success": True,
        "message": "Registration successful.",
        "user_id": str(result.inserted_id)
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"success": False, "error": "Invalid input types."}), 400

    user = users.find_one({"email": email.strip().lower()})

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({
            "success": False,
            "error": "Invalid email or password."
        }), 401

    session.clear()
    session["user_id"] = str(user["_id"])

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def current_user():
    try:
        user = users.find_one({
            "_id": ObjectId(session["user_id"])
        })
    except Exception:
        session.clear()
        return jsonify({"success": False, "error": "Invalid session."}), 401

    if not user:
        session.clear()
        return jsonify({"success": False, "error": "User not found."}), 401

    return jsonify({
        "success": True,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }
    }), 200
