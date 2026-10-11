import os
from pathlib import Path

from chat_history import chat_bp
from dotenv import load_dotenv

from flask import Flask, request, jsonify, render_template, session
from auth import auth_bp, login_required
from flask_cors import CORS
from werkzeug.utils import secure_filename

from document_processing.processor import process_pdf
from document_processing.embeddings import generate_embeddings
from document_processing.vector_store import VectorStore
from rag.pipeline import RAGPipeline


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# GEMINI API KEY
# =========================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


if not GEMINI_API_KEY:

    print(
        "WARNING: GEMINI_API_KEY is not loaded."
    )

else:

    print(
        "Gemini API key loaded successfully."
    )


# =========================================================
# FLASK APPLICATION
# =========================================================


app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY is missing from .env")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

CORS(app, supports_credentials=True)

app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)



# =========================================================
# APPLICATION SETTINGS
# =========================================================

# Maximum PDF size = 20 MB

app.config["MAX_CONTENT_LENGTH"] = (
    20 * 1024 * 1024
)


# =========================================================
# UPLOAD FOLDER
# =========================================================

UPLOAD_FOLDER = Path(
    "uploads"
)

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = str(
    UPLOAD_FOLDER
)


# =========================================================
# ALLOWED FILE TYPES
# =========================================================

ALLOWED_EXTENSIONS = {
    "pdf"
}


def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# VECTOR STORE
# =========================================================

# all-MiniLM-L6-v2
# produces 384-dimensional embeddings

EMBEDDING_DIMENSION = 384


user_vector_stores = {}
user_documents = {}


def get_user_vector_store(user_id):
    if user_id not in user_vector_stores:
        user_vector_stores[user_id] = VectorStore(
            dimension=EMBEDDING_DIMENSION
        )

    return user_vector_stores[user_id]


# =========================================================
# HOME PAGE
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():
    return jsonify({
        "status": "healthy",
        "message": "AI Document Q&A Assistant is running."
    }), 200




# =========================================================
# UPLOAD DOCUMENT
# =========================================================

@app.route("/upload", methods=["POST"])
@login_required
def upload_document():

    user_id = session["user_id"]

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No file provided."
        }), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({
            "success": False,
            "error": "No file selected."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Only PDF files are allowed."
        }), 400

    filename = secure_filename(file.filename)

    if not filename:
        return jsonify({
            "success": False,
            "error": "Invalid filename."
        }), 400

    user_folder = UPLOAD_FOLDER / user_id
    user_folder.mkdir(parents=True, exist_ok=True)

    file_path = user_folder / filename

    try:
        file.save(str(file_path))

        chunks = process_pdf(str(file_path))

        if not chunks:
            file_path.unlink(missing_ok=True)
            return jsonify({
                "success": False,
                "error": "No readable text found in PDF."
            }), 400

        texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings(texts)

        store = VectorStore(dimension=EMBEDDING_DIMENSION)
        store.add(embeddings, chunks)

        user_vector_stores[user_id] = store
        user_documents[user_id] = {
            "filename": filename,
            "chunks": len(chunks)
        }

        return jsonify({
            "success": True,
            "message": "Document uploaded and processed successfully.",
            "filename": filename,
            "chunks_created": len(chunks)
        }), 200

    except Exception:
        app.logger.exception("Document upload failed")

        return jsonify({
            "success": False,
            "error": "Failed to process document."
        }), 500



@app.route("/ask", methods=["POST"])
@login_required
def ask_question():
    user_id = session["user_id"]

    data = request.get_json(silent=True) or {}
    question = data.get("question", "")

    if not isinstance(question, str) or not question.strip():
        return jsonify({
            "success": False,
            "error": "A valid question is required."
        }), 400

    question = question.strip()

    store = user_vector_stores.get(user_id)
    document = user_documents.get(user_id)

    if store is None or not store.metadata or document is None:
        return jsonify({
            "success": False,
            "error": "Please upload your PDF first."
        }), 400

    try:
        rag_pipeline = RAGPipeline(store)
        answer = rag_pipeline.answer(question, top_k=5)

        return jsonify({
            "success": True,
            "question": question,
            "answer": answer,
            "filename": document["filename"]
        }), 200

    except Exception:
        app.logger.exception("Question answering failed")

        return jsonify({
            "success": False,
            "error": "Failed to generate an answer."
        }), 500

# =========================================================
# FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    return jsonify({

        "success": False,

        "error":
            "File is too large. Maximum allowed size is 20 MB."

    }), 413


# =========================================================
# METHOD NOT ALLOWED
# =========================================================

@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "success": False,

        "error":
            "HTTP method not allowed."

    }), 405


# =========================================================
# INTERNAL SERVER ERROR
# =========================================================

@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "success": False,

        "error":
            "Internal server error."

    }), 500


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print("        DOCUMIND AI")
    print("  AI DOCUMENT Q&A ASSISTANT")
    print("=" * 65)

    print(
        "Server : http://127.0.0.1:5000"
    )

    print(
        "Health : http://127.0.0.1:5000/health"
    )

    print(
        "Upload : POST /upload"
    )

    print(
        "Ask    : POST /ask"
    )

    print("=" * 65)
    print()


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )

