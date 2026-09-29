from .retriever import Retriever
from .prompt import build_prompt
from .llm import GeminiLLM


class RAGPipeline:
    def __init__(self, vector_store):
        self.retriever = Retriever(vector_store)
        self.llm = GeminiLLM()

    def answer(self, question, top_k=5):
        retrieved_chunks = self.retriever.retrieve(
            question,
            top_k=top_k
        )

        if not retrieved_chunks:
            return "I could not find the answer in the provided documents."

        prompt = build_prompt(
            question,
            retrieved_chunks
        )

        return self.llm.generate(prompt)