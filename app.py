import os
from pathlib import Path

from dotenv import load_dotenv

from flask import Flask, request, jsonify, render_template
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

CORS(app)


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


vector_store = VectorStore(
    dimension=EMBEDDING_DIMENSION
)


# =========================================================
# CURRENT DOCUMENT INFORMATION
# =========================================================

current_document = {
    "filename": None,
    "chunks": 0
}


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

        "message":
            "AI Document Q&A Assistant is running.",

        "document_loaded":
            len(vector_store.metadata) > 0

    }), 200


# =========================================================
# UPLOAD DOCUMENT
# =========================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_document():

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if "file" not in request.files:

        return jsonify({

            "success": False,

            "error":
                "No file provided."

        }), 400


    # -----------------------------------------------------
    # Get file
    # -----------------------------------------------------

    file = request.files["file"]


    # -----------------------------------------------------
    # Check filename
    # -----------------------------------------------------

    if not file.filename:

        return jsonify({

            "success": False,

            "error":
                "No file selected."

        }), 400


    # -----------------------------------------------------
    # Check extension
    # -----------------------------------------------------

    if not allowed_file(
        file.filename
    ):

        return jsonify({

            "success": False,

            "error":
                "Only PDF files are allowed."

        }), 400


    # -----------------------------------------------------
    # Secure filename
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )


    if not filename:

        return jsonify({

            "success": False,

            "error":
                "Invalid filename."

        }), 400


    # -----------------------------------------------------
    # File path
    # -----------------------------------------------------

    file_path = (
        UPLOAD_FOLDER /
        filename
    )


    try:

        print()
        print("=" * 65)
        print("DOCUMENT UPLOAD")
        print("=" * 65)

        print(
            f"File: {filename}"
        )


        # -------------------------------------------------
        # Save file
        # -------------------------------------------------

        file.save(
            str(file_path)
        )

        print(
            "✓ PDF saved"
        )


        # -------------------------------------------------
        # Process PDF
        # -------------------------------------------------

        print(
            "→ Extracting text..."
        )

        chunks = process_pdf(
            str(file_path)
        )


        # -------------------------------------------------
        # Check chunks
        # -------------------------------------------------

        if not chunks:

            return jsonify({

                "success": False,

                "error":
                    "No readable text found in PDF."

            }), 400


        print(
            f"✓ {len(chunks)} chunks created"
        )


        # -------------------------------------------------
        # Extract text
        # -------------------------------------------------

        texts = [
            chunk["text"]
            for chunk in chunks
        ]


        # -------------------------------------------------
        # Generate embeddings
        # -------------------------------------------------

        print(
            "→ Generating embeddings..."
        )

        embeddings = generate_embeddings(
            texts
        )


        print(
            "✓ Embeddings generated"
        )


        # -------------------------------------------------
        # Clear previous document
        # -------------------------------------------------

        print(
            "→ Preparing vector store..."
        )


        # Your VectorStore may expose either
        # reset() or clear().

        if hasattr(
            vector_store,
            "reset"
        ):

            vector_store.reset()

            print(
                "✓ Previous document cleared"
            )

        elif hasattr(
            vector_store,
            "clear"
        ):

            vector_store.clear()

            print(
                "✓ Previous document cleared"
            )

        else:

            print(
                "ℹ VectorStore has no reset/clear method."
            )


        # -------------------------------------------------
        # Add embeddings
        # -------------------------------------------------

        print(
            "→ Adding embeddings to FAISS..."
        )

        vector_store.add(
            embeddings,
            chunks
        )


        print(
            "✓ Document indexed successfully"
        )


        # -------------------------------------------------
        # Update current document
        # -------------------------------------------------

        current_document[
            "filename"
        ] = filename

        current_document[
            "chunks"
        ] = len(chunks)


        print("=" * 65)
        print(
            "DOCUMENT READY"
        )
        print("=" * 65)
        print()


        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "message":
                "Document uploaded and processed successfully.",

            "filename":
                filename,

            "chunks_created":
                len(chunks)

        }), 200


    except Exception as e:

        print()
        print("=" * 65)
        print("UPLOAD ERROR")
        print("=" * 65)

        print(
            str(e)
        )

        print("=" * 65)
        print()


        return jsonify({

            "success": False,

            "error":
                f"Failed to process document: {str(e)}"

        }), 500


# =========================================================
# ASK QUESTION
# =========================================================

@app.route(
    "/ask",
    methods=["POST"]
)
def ask_question():

    # -----------------------------------------------------
    # Read JSON
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({

            "success": False,

            "error":
                "Request body is required."

        }), 400


    # -----------------------------------------------------
    # Get question
    # -----------------------------------------------------

    question = data.get(
        "question",
        ""
    )


    # -----------------------------------------------------
    # Validate type
    # -----------------------------------------------------

    if not isinstance(
        question,
        str
    ):

        return jsonify({

            "success": False,

            "error":
                "Question must be a string."

        }), 400


    question = question.strip()


    # -----------------------------------------------------
    # Validate question
    # -----------------------------------------------------

    if not question:

        return jsonify({

            "success": False,

            "error":
                "Question is required."

        }), 400


    # -----------------------------------------------------
    # Check document
    # -----------------------------------------------------

    if len(
        vector_store.metadata
    ) == 0:

        return jsonify({

            "success": False,

            "error":
                "Please upload a document first."

        }), 400


    try:

        print()
        print("=" * 65)
        print("QUESTION")
        print("=" * 65)

        print(
            question
        )


        # -------------------------------------------------
        # Create RAG pipeline
        # -------------------------------------------------

        rag_pipeline = RAGPipeline(
            vector_store
        )


        # -------------------------------------------------
        # Retrieve + Generate
        # -------------------------------------------------

        print(
            "→ Running RAG pipeline..."
        )


        answer = rag_pipeline.answer(
            question,
            top_k=5
        )


        print(
            "✓ Answer generated"
        )


        print("=" * 65)
        print()


        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "question":
                question,

            "answer":
                answer,

            "filename":
                current_document[
                    "filename"
                ]

        }), 200


    except Exception as e:

        print()
        print("=" * 65)
        print("QUESTION ERROR")
        print("=" * 65)

        print(
            str(e)
        )

        print("=" * 65)
        print()


        return jsonify({

            "success": False,

            "error":
                f"Failed to generate answer: {str(e)}"

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

