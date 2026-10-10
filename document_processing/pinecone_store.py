
import os
import hashlib

from pinecone import Pinecone
from document_processing.embeddings import generate_embeddings


class PineconeVectorStore:
    def __init__(self, api_key=None, index_name=None):
        api_key = api_key or os.getenv("PINECONE_API_KEY")
        index_name = index_name or os.getenv("PINECONE_INDEX_NAME")

        if not api_key:
            raise ValueError("PINECONE_API_KEY is missing")

        if not index_name:
            raise ValueError("PINECONE_INDEX_NAME is missing")

        self.client = Pinecone(api_key=api_key)
        self.index = self.client.Index(index_name)

    def index_chunks(self, chunks, user_id, document_id):
        """Generate embeddings and store processed PDF chunks."""

        if not user_id or not document_id:
            raise ValueError("user_id and document_id are required")

        valid_chunks = [
            chunk for chunk in chunks
            if chunk.get("text", "").strip()
        ]

        if not valid_chunks:
            return 0

        texts = [chunk["text"] for chunk in valid_chunks]
        embeddings = generate_embeddings(texts)

        vectors = []

        for chunk, embedding in zip(valid_chunks, embeddings):
            chunk_id = str(chunk["chunk_id"])

            unique_id = hashlib.sha256(
                f"{user_id}:{document_id}:{chunk_id}".encode()
            ).hexdigest()

            metadata = {
                "user_id": str(user_id),
                "document_id": str(document_id),
                "chunk_id": chunk_id,
                "text": chunk["text"],
                "document": str(chunk.get("document", document_id)),
                "page": int(chunk.get("page", 1)),
            }

            vectors.append({
                "id": unique_id,
                "values": embedding.tolist(),
                "metadata": metadata,
            })

        # Upsert in batches of 100 vectors.
        for start in range(0, len(vectors), 100):
            self.index.upsert(
                vectors=vectors[start:start + 100]
            )

        return len(vectors)

    def search(self, query, user_id, top_k=5, document_id=None):
        """Retrieve relevant chunks for a particular user."""

        if not user_id:
            raise ValueError("user_id is required")

        query_embedding = generate_embeddings([query])[0]

        metadata_filter = {
            "user_id": {"$eq": str(user_id)}
        }

        if document_id:
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
            metadata = match.metadata or {}

            results.append({
                "score": float(match.score or 0),
                **metadata,
            })

        return results

    def delete_document(self, document_id, user_id):
        """Delete only this user's vectors for the specified document."""

        if not user_id or not document_id:
            raise ValueError("user_id and document_id are required")

        self.index.delete(
            filter={
                "user_id": {"$eq": str(user_id)},
                "document_id": {"$eq": str(document_id)},
            }
        )
