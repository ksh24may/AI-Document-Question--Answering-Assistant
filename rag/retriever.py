from document_processing.embeddings import generate_embeddings
from document_processing.vector_store import VectorStore


class Retriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve(self, question, top_k=5):
        query_embedding = generate_embeddings([question])[0]

        results = self.vector_store.search(
            query_embedding,
            top_k=top_k
        )

        return results