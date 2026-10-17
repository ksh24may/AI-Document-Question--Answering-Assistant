
from .retriever import Retriever
from .prompt import build_prompt
from .llm import GeminiLLM


class RAGPipeline:
    """Retrieve relevant document chunks and generate answers."""

    def __init__(self, vector_store, user_id, document_id=None):
        self.retriever = Retriever(
            vector_store=vector_store,
            user_id=user_id,
            document_id=document_id,
        )
        self.llm = GeminiLLM()

    def answer(self, question, top_k=5):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty")

        retrieved_chunks = self.retriever.retrieve(
            question,
            top_k=top_k,
        )

        if not retrieved_chunks:
            return (
                "I could not find the answer "
                "in the provided documents."
            )

        prompt = build_prompt(
            question,
            retrieved_chunks,
        )

        return self.llm.generate(prompt)