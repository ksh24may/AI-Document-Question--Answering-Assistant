
class Retriever:
    """Retrieve relevant PDF chunks from Pinecone."""

    def __init__(self, vector_store, user_id, document_id=None):
        self.vector_store = vector_store
        self.user_id = user_id
        self.document_id = document_id

    def retrieve(self, question, top_k=5):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty")

        if not self.user_id:
            raise ValueError("user_id is required")

        results = self.vector_store.search(
            query=question,
            user_id=self.user_id,
            top_k=top_k,
            document_id=self.document_id,
        )

        return results
