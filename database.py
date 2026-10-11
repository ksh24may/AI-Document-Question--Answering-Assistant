
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_document_qa")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[MONGO_DB_NAME]

users = db["users"]
conversations = db["conversations"]
messages = db["messages"]

users.create_index("email", unique=True)
conversations.create_index(
    [("user_id", ASCENDING), ("created_at", ASCENDING)]
)
messages.create_index(
    [("user_id", ASCENDING), ("conversation_id", ASCENDING)]
)
conversations.create_index(
    "created_at",
    expireAfterSeconds=604800,
    name="conversations_7_day_ttl"
)

messages.create_index(
    "created_at",
    expireAfterSeconds=604800,
    name="messages_7_day_ttl"
)

def test_connection():
    client.admin.command("ping")
    print("MongoDB connected successfully!")
    print("Database:", MONGO_DB_NAME)
    print("Collections:", db.list_collection_names())

if __name__ == "__main__":
    test_connection()
