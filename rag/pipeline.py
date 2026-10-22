
from .retriever import Retriever
from .prompt import build_prompt, build_insights_prompt
from .llm import GeminiLLM


class RAGPipeline:
    def __init__(self, vector_store):
        self.retriever = Retriever(vector_store)
        self.llm = GeminiLLM()

    def answer(self, question, top_k=5, learning_level="student"):
        """
        Answer a question using retrieved document chunks.

        learning_level can be: beginner, student, or expert.
        """
        retrieved_chunks = self.retriever.retrieve(
            question,
            top_k=top_k
        )

        if not retrieved_chunks:
            return (
                "I could not find the answer "
                "in the provided documents."
            )

        prompt = build_prompt(
            question,
            retrieved_chunks,
            learning_level=learning_level
        )

        return self.llm.generate(prompt)

    def generate_insights(self, top_k=8):
        """
        Generate structured insights from document excerpts.
        """
        query = (
            "Summarize the main topics, key findings, "
            "important concepts, and technical terms "
            "in this document."
        )

        retrieved_chunks = self.retriever.retrieve(
            query,
            top_k=top_k
        )

        if not retrieved_chunks:
            return (
                '{"summary":"Could not find enough information '
                'in the document.","key_takeaways":[],'
                '"important_terms":[],"major_findings":[]}'
            )

        prompt = build_insights_prompt(retrieved_chunks)

        return self.llm.generate(prompt)
