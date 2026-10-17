
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from flask import Blueprint, jsonify, request, session

from database import conversations, messages
from auth import login_required

chat_bp = Blueprint("chat_history", __name__, url_prefix="/api")


def get_current_user_id():
    return session.get("user_id")


def get_cutoff_time():
    return datetime.now(timezone.utc) - timedelta(days=7)


def serialize_document(document):
    return {
        "id": str(document["_id"]),
        "title": document.get("title", ""),
        "created_at": document["created_at"].isoformat(),
        "updated_at": document.get(
            "updated_at", document["created_at"]
        ).isoformat()
    }


def serialize_message(message):
    return {
        "id": str(message["_id"]),
        "conversation_id": message["conversation_id"],
        "role": message["role"],
        "content": message["content"],
        "created_at": message["created_at"].isoformat()
    }


@chat_bp.route("/conversations", methods=["POST"])
@login_required
def create_conversation():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "New conversation")

    if not isinstance(title, str):
        return jsonify({
            "success": False,
            "error": "Title must be a string."
        }), 400

    now = datetime.now(timezone.utc)

    conversation = {
        "user_id": get_current_user_id(),
        "title": title.strip()[:200] or "New conversation",
        "created_at": now,
        "updated_at": now
    }

    result = conversations.insert_one(conversation)

    return jsonify({
        "success": True,
        "conversation_id": str(result.inserted_id),
        "title": conversation["title"],
        "created_at": now.isoformat()
    }), 201


@chat_bp.route("/conversations", methods=["GET"])
@login_required
def get_conversations():
    cutoff = get_cutoff_time()

    cursor = conversations.find({
        "user_id": get_current_user_id(),
        "created_at": {"$gte": cutoff}
    }).sort("updated_at", -1)

    return jsonify({
        "success": True,
        "conversations": [
            serialize_document(conversation)
            for conversation in cursor
        ]
    }), 200


@chat_bp.route(
    "/conversations/<conversation_id>/messages",
    methods=["POST"]
)
@login_required
def save_message(conversation_id):
    if not ObjectId.is_valid(conversation_id):
        return jsonify({
            "success": False,
            "error": "Invalid conversation ID."
        }), 400

    cutoff = get_cutoff_time()

    conversation = conversations.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": get_current_user_id(),
        "created_at": {"$gte": cutoff}
    })

    if not conversation:
        return jsonify({
            "success": False,
            "error": "Conversation not found or access denied."
        }), 404

    data = request.get_json(silent=True) or {}
    role = data.get("role")
    content = data.get("content")

    if role not in ("user", "assistant"):
        return jsonify({
            "success": False,
            "error": "Role must be user or assistant."
        }), 400

    if not isinstance(content, str) or not content.strip():
        return jsonify({
            "success": False,
            "error": "Message content is required."
        }), 400

    now = datetime.now(timezone.utc)

    message = {
        "user_id": get_current_user_id(),
        "conversation_id": conversation_id,
        "role": role,
        "content": content.strip(),
        "created_at": now
    }

    result = messages.insert_one(message)

    conversations.update_one(
        {
            "_id": ObjectId(conversation_id),
            "user_id": get_current_user_id()
        },
        {"$set": {"updated_at": now}}
    )

    return jsonify({
        "success": True,
        "message_id": str(result.inserted_id),
        "created_at": now.isoformat()
    }), 201


@chat_bp.route(
    "/conversations/<conversation_id>/messages",
    methods=["GET"]
)
@login_required
def get_messages(conversation_id):
    if not ObjectId.is_valid(conversation_id):
        return jsonify({
            "success": False,
            "error": "Invalid conversation ID."
        }), 400

    cutoff = get_cutoff_time()

    conversation = conversations.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": get_current_user_id(),
        "created_at": {"$gte": cutoff}
    })

    if not conversation:
        return jsonify({
            "success": False,
            "error": "Conversation not found or access denied."
        }), 404

    cursor = messages.find({
        "user_id": get_current_user_id(),
        "conversation_id": conversation_id,
        "created_at": {"$gte": cutoff}
    }).sort("created_at", 1)

    return jsonify({
        "success": True,
        "conversation": serialize_document(conversation),
        "messages": [
            serialize_message(message)
            for message in cursor
        ]
    }), 200
