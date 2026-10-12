import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import fitz
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from werkzeug.utils import secure_filename

from auth import auth_bp, login_required
from chat_history import chat_bp
from database import conversations
from document_processing.processor import process_pdf
from document_processing.embeddings import generate_embeddings
from document_processing.vector_store import VectorStore
from rag.pipeline import RAGPipeline


load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    print("WARNING: GEMINI_API_KEY is not loaded.")
else:
    print("Gemini API key loaded successfully.")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY is missing from .env")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

CORS(app, supports_credentials=True)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)

MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_PDF_PAGES = 50
EMBEDDING_DIMENSION = 384

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = (BASE_DIR / "uploads").resolve()
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# FAISS indexes are rebuilt from each conversation's saved PDF after a restart.
conversation_vector_stores = {}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


def get_owned_conversation(conversation_id, user_id):
    if not isinstance(conversation_id, str) or not ObjectId.is_valid(conversation_id):
        return None

    return conversations.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": user_id,
    })


def get_safe_pdf_path(conversation, user_id):
    document = conversation.get("document")
    if not document or not document.get("path"):
        return None

    user_folder = (UPLOAD_FOLDER / user_id).resolve()
    pdf_path = Path(document["path"]).resolve()

    if not pdf_path.is_relative_to(user_folder):
        raise ValueError("Invalid saved PDF path.")

    return pdf_path


def build_vector_store(pdf_path, source_filename=None):
    """Validate a PDF and create its in-memory FAISS index."""
    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.is_relative_to(UPLOAD_FOLDER):
        raise ValueError("Invalid PDF path.")
    if not pdf_path.is_file():
        raise FileNotFoundError("The PDF file could not be found.")
    if pdf_path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("PDF exceeds the 20 MB limit.")

    try:
        with fitz.open(str(pdf_path)) as pdf:
            page_count = len(pdf)
    except Exception as exc:
        raise ValueError("The uploaded file is not a valid or readable PDF.") from exc

    if page_count == 0:
        raise ValueError("The PDF contains no pages.")
    if page_count > MAX_PDF_PAGES:
        raise ValueError("PDF exceeds the 50-page limit.")

    chunks = process_pdf(str(pdf_path))
    if not chunks:
        raise ValueError("No readable text found in PDF.")

    # Keep the original uploaded filename in source metadata.
    display_name = source_filename or pdf_path.name
    for chunk in chunks:
        chunk["document"] = display_name

    embeddings = generate_embeddings([chunk["text"] for chunk in chunks])
    embeddings = embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings

    store = VectorStore(dimension=EMBEDDING_DIMENSION)
    store.add(embeddings, chunks)

    return store, page_count, len(chunks)


def load_conversation_store(conversation, user_id):
    conversation_id = str(conversation["_id"])

    if not conversation.get("document"):
        return None

    cached_store = conversation_vector_stores.get(conversation_id)
    if cached_store is not None:
        return cached_store

    pdf_path = get_safe_pdf_path(conversation, user_id)
    if pdf_path is None:
        return None

    store, page_count, chunk_count = build_vector_store(
        pdf_path,
        source_filename=(
            conversation["document"].get("filename") or pdf_path.name
        ),
    )

    conversation_vector_stores[conversation_id] = store

    conversations.update_one(
        {"_id": conversation["_id"], "user_id": user_id},
        {"$set": {
            "document.pages": page_count,
            "document.chunks": chunk_count,
        }},
    )

    return store


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "message": "AI Document Q&A Assistant is running.",
    })


@app.route("/api/conversations/<conversation_id>/document")
@login_required
def get_document_status(conversation_id):
    user_id = session["user_id"]
    conversation = get_owned_conversation(conversation_id, user_id)

    if not conversation:
        return jsonify({
            "success": False,
            "error": "Conversation not found.",
        }), 404

    document = conversation.get("document")

    if document:
        try:
            pdf_path = get_safe_pdf_path(conversation, user_id)
            if pdf_path is None or not pdf_path.is_file():
                document = None
        except ValueError:
            app.logger.exception("Invalid saved PDF path")
            return jsonify({
                "success": False,
                "error": "Invalid saved PDF path.",
            }), 400

    return jsonify({
        "success": True,
        "document": (
            {
                "filename": document.get("filename"),
                "pages": document.get("pages"),
                "chunks": document.get("chunks"),
            }
            if document else None
        ),
    })


@app.route("/upload", methods=["POST"])
@login_required
def upload_document():
    user_id = session["user_id"]

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No file provided.",
        }), 400

    uploaded_file = request.files["file"]

    if not uploaded_file.filename:
        return jsonify({
            "success": False,
            "error": "No file selected.",
        }), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({
            "success": False,
            "error": "Only PDF files are allowed.",
        }), 400

    filename = secure_filename(uploaded_file.filename)

    if not filename:
        return jsonify({
            "success": False,
            "error": "Invalid filename.",
        }), 400

    conversation_id = request.form.get("conversation_id", "")
    conversation = get_owned_conversation(conversation_id, user_id)

    if not conversation:
        return jsonify({
            "success": False,
            "error": "Create or select a conversation before uploading.",
        }), 400

    user_folder = (UPLOAD_FOLDER / user_id).resolve()
    user_folder.mkdir(parents=True, exist_ok=True)

    pdf_path = (user_folder / f"{conversation_id}.pdf").resolve()

    if not pdf_path.is_relative_to(user_folder):
        return jsonify({
            "success": False,
            "error": "Invalid upload path.",
        }), 400

    previous_document = conversation.get("document")
    previous_store = conversation_vector_stores.get(conversation_id)

    temp_path = None
    backup_path = None
    target_replaced = False
    metadata_updated = False

    try:
        # Save and process the new PDF without touching the existing PDF.
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".pdf",
            prefix=f".{conversation_id}.upload-",
            dir=str(user_folder),
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name).resolve()
            uploaded_file.save(temp_file)

        store, page_count, chunk_count = build_vector_store(
            temp_path,
            source_filename=filename,
        )

        document = {
            "filename": filename,
            "path": str(pdf_path),
            "pages": page_count,
            "chunks": chunk_count,
        }

        # Move the previous PDF to a backup before installing the new one.
        if pdf_path.exists():
            backup_path = user_folder / f".{conversation_id}.backup.pdf"
            if backup_path.exists():
                backup_path.unlink()
            os.replace(str(pdf_path), str(backup_path))

        os.replace(str(temp_path), str(pdf_path))
        temp_path = None
        target_replaced = True

        result = conversations.update_one(
            {"_id": conversation["_id"], "user_id": user_id},
            {"$set": {
                "document": document,
                "updated_at": datetime.now(timezone.utc),
            }},
        )

        if result.matched_count != 1:
            raise RuntimeError("Could not save PDF information.")

        metadata_updated = True
        conversation_vector_stores[conversation_id] = store

        if backup_path and backup_path.exists():
            backup_path.unlink()
            backup_path = None

        return jsonify({
            "success": True,
            "message": "Document uploaded and processed successfully.",
            "filename": filename,
            "pages": page_count,
            "chunks_created": chunk_count,
            "conversation_id": conversation_id,
        })

    except Exception as error:
        app.logger.exception("Document upload failed")

        try:
            # Restore the old file if the replacement did not complete.
            if target_replaced and pdf_path.exists():
                pdf_path.unlink()

            if backup_path and backup_path.exists():
                os.replace(str(backup_path), str(pdf_path))
                backup_path = None

            if previous_document:
                conversations.update_one(
                    {"_id": conversation["_id"], "user_id": user_id},
                    {"$set": {"document": previous_document}},
                )
            elif metadata_updated:
                conversations.update_one(
                    {"_id": conversation["_id"], "user_id": user_id},
                    {"$unset": {"document": ""}},
                )

            if previous_store is not None:
                conversation_vector_stores[conversation_id] = previous_store
            else:
                conversation_vector_stores.pop(conversation_id, None)

        except Exception:
            app.logger.exception("Could not restore previous document state")

        message = (
            str(error)
            if isinstance(error, (ValueError, FileNotFoundError))
            else "Failed to process document. Check the Flask terminal."
        )

        status_code = (
            400 if isinstance(error, (ValueError, FileNotFoundError)) else 500
        )

        return jsonify({
            "success": False,
            "error": message,
        }), status_code

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


@app.route("/ask", methods=["POST"])
@login_required
def ask_question():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}

    question_text = data.get("question", "")
    conversation_id = data.get("conversation_id", "")

    if not isinstance(question_text, str) or not question_text.strip():
        return jsonify({
            "success": False,
            "error": "A valid question is required.",
        }), 400

    conversation = get_owned_conversation(conversation_id, user_id)

    if not conversation:
        return jsonify({
            "success": False,
            "error": "Conversation not found.",
        }), 404

    try:
        store = load_conversation_store(conversation, user_id)

        if store is None:
            return jsonify({
                "success": False,
                "error": "Upload a PDF to this conversation first.",
            }), 400

        answer_text = RAGPipeline(store).answer(
            question_text.strip(),
            top_k=5,
        )

        return jsonify({
            "success": True,
            "question": question_text.strip(),
            "answer": answer_text,
            "filename": conversation["document"]["filename"],
            "conversation_id": conversation_id,
        })

    except FileNotFoundError:
        app.logger.exception("Saved PDF is missing")
        return jsonify({
            "success": False,
            "error": "Saved PDF is missing. Please upload it again.",
        }), 404

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400

    except Exception:
        app.logger.exception("Question answering failed")
        return jsonify({
            "success": False,
            "error": "Failed to generate an answer. Check the Flask terminal.",
        }), 500


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "success": False,
        "error": "File is too large. Maximum allowed size is 20 MB.",
    }), 413


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "HTTP method not allowed.",
    }), 405


if __name__ == "__main__":
    print("=" * 60)
    print("DOCUMIND AI")
    print("Server: http://127.0.0.1:5000")
    print(f"PDF limit: {MAX_PDF_PAGES} pages, 20 MB")
    print("=" * 60)

    app.run(host="127.0.0.1", port=5000, debug=True)