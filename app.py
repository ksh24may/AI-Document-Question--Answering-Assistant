
import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from document_processing.processor import process_pdf
from document_processing.embeddings import generate_embeddings
from document_processing.vector_store import VectorStore
from rag.pipeline import RAGPipeline


# --------------------------------------------------
# Check Gemini API key
# --------------------------------------------------

if not os.getenv("GEMINI_API_KEY"):
    print("WARNING: GEMINI_API_KEY is not loaded.")
else:
    print("Gemini API key loaded successfully.")


# --------------------------------------------------
# Flask application
# --------------------------------------------------

app = Flask(__name__)
CORS(app)


# --------------------------------------------------
# Upload folder
# --------------------------------------------------

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)


# --------------------------------------------------
# Allowed files
# --------------------------------------------------

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# --------------------------------------------------
# Vector store
# all-MiniLM-L6-v2 = 384 dimensions
# --------------------------------------------------

EMBEDDING_DIMENSION = 384

vector_store = VectorStore(
    dimension=EMBEDDING_DIMENSION
)


# --------------------------------------------------
# Home API
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "AI Document Question Answering Assistant API",
        "status": "running"
    })


# --------------------------------------------------
# Health API
# --------------------------------------------------

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "healthy"
    })


# --------------------------------------------------
# Upload PDF
# --------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload_document():

    if "file" not in request.files:

        return jsonify({
            "error": "No file provided."
        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({
            "error": "No file selected."
        }), 400

    if not allowed_file(file.filename):

        return jsonify({
            "error": "Only PDF files are allowed."
        }), 400

    filename = secure_filename(file.filename)

    file_path = UPLOAD_FOLDER / filename

    try:

        # ------------------------------------------
        # Save PDF
        # ------------------------------------------

        file.save(file_path)

        # ------------------------------------------
        # PDF -> text -> chunks
        # ------------------------------------------

        chunks = process_pdf(
            str(file_path)
        )

        if not chunks:

            return jsonify({
                "error": "No readable text found in PDF."
            }), 400

        # ------------------------------------------
        # Extract chunk text
        # ------------------------------------------

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        # ------------------------------------------
        # Generate embeddings
        # ------------------------------------------

        embeddings = generate_embeddings(
            texts
        )

        # ------------------------------------------
        # Store embeddings in FAISS
        # ------------------------------------------

        vector_store.add(
            embeddings,
            chunks
        )

        return jsonify({

            "message":
                "Document uploaded and processed successfully.",

            "filename":
                filename,

            "chunks_created":
                len(chunks)

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# --------------------------------------------------
# Ask question
# --------------------------------------------------

@app.route("/ask", methods=["POST"])
def ask_question():

    # ----------------------------------------------
    # Read JSON request
    # ----------------------------------------------

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required."
        }), 400

    # ----------------------------------------------
    # Get question
    # ----------------------------------------------

    question = data.get(
        "question",
        ""
    ).strip()

    if not question:

        return jsonify({
            "error": "Question is required."
        }), 400

    # ----------------------------------------------
    # Check whether a document exists
    # ----------------------------------------------

    if len(vector_store.metadata) == 0:

        return jsonify({
            "error":
                "Please upload a document first."
        }), 400

    try:

        # ------------------------------------------
        # Create RAG pipeline
        # ------------------------------------------

        rag_pipeline = RAGPipeline(
            vector_store
        )

        # ------------------------------------------
        # Retrieve + generate answer
        # ------------------------------------------

        answer = rag_pipeline.answer(
            question,
            top_k=5
        )

        # ------------------------------------------
        # Return response
        # ------------------------------------------

        return jsonify({

            "question":
                question,

            "answer":
                answer

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# --------------------------------------------------
# Start server
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

