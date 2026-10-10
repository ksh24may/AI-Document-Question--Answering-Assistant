
import os
import hashlib

from dotenv import load_dotenv
from pinecone import Pinecone

from document_processing.embeddings import generate_embeddings

load_dotenv()


class PineconeVectorStore:
    """Store and search PDF chunk embeddings in Pinecone."""

    def __init__(self, api_key=None, index_name=None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_name = (
            index_name or os.getenv("PINECONE_INDEX_NAME")
        )

        if not self.api_key:
            raise ValueError("PINECONE_API_KEY is missing")

        if not self.index_name:
            raise ValueError("PINECONE_INDEX_NAME is missing")

        self.client = Pinecone(api_key=self.api_key)
        self.index = self.client.Index(self.index_name)

    @staticmethod
    def _vector_id(user_id, document_id, chunk_id):
        """Generate a stable, unique ID for each document chunk."""
        value = f"{user_id}:{document_id}:{chunk_id}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def index_chunks(self, chunks, user_id, document_id):
        """
        Embed processed PDF chunks and store them in Pinecone.

        Each chunk should contain:
        text, document, page, and chunk_id.
        Returns the number of indexed chunks.
        """
        if not user_id or not document_id:
            raise ValueError("user_id and document_id are required")

        valid_chunks = [
            chunk
            for chunk in chunks
            if isinstance(chunk.get("text"), str)
            and chunk["text"].strip()
        ]

        if not valid_chunks:
            return 0

        for chunk in valid_chunks:
            if "chunk_id" not in chunk:
                raise ValueError("Every chunk must have a chunk_id")

        texts = [chunk["text"] for chunk in valid_chunks]
        embeddings = generate_embeddings(texts)

        vectors = []

        for chunk, embedding in zip(valid_chunks, embeddings):
            chunk_id = str(chunk["chunk_id"])

            metadata = {
                "user_id": str(user_id),
                "document_id": str(document_id),
                "chunk_id": chunk_id,
                "text": chunk["text"],
                "document": str(chunk.get("document", document_id)),
                "page": int(chunk.get("page", 1)),
            }

            vectors.append({
                "id": self._vector_id(
                    user_id, document_id, chunk_id
                ),
                "values": embedding.tolist(),
                "metadata": metadata,
            })

        # Upsert vectors in batches.
        for start in range(0, len(vectors), 100):
            batch = vectors[start:start + 100]
            self.index.upsert(vectors=batch)

        return len(vectors)

    def search(
        self,
        query,
        user_id,
        top_k=5,
        document_id=None,
    ):
        """
        Retrieve the most relevant chunks for a user's question.
        Optionally restrict search to one document.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query cannot be empty")

        if not user_id:
            raise ValueError("user_id is required")

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")

        query_embedding = generate_embeddings([query])[0]

        metadata_filter = {
            "user_id": {"$eq": str(user_id)}
        }

        if document_id is not None:
            metadata_filter["document_id"] = {
                "$eq": str(document_id)
            }

        response = self.index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            filter=metadata_filter,
            include_metadata=True,
        )

        results = []

        for match in response.matches:
            metadata = dict(match.metadata or {})

            results.append({
                "score": float(match.score or 0.0),
                **metadata,
            })

        return results

    def delete_document(self, document_id, user_id):
        """
        Delete all vectors belonging to a specific user's document.
        """
        if not user_id or not document_id:
            raise ValueError(
                "user_id and document_id are required"
            )

        self.index.delete(
            filter={
                "user_id": {"$eq": str(user_id)},
                "document_id": {"$eq": str(document_id)},
            }
        )
