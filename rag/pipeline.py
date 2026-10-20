
from .retriever import Retriever
from .prompt import build_prompt
from .llm import GeminiLLM
from .insights import (
    generate_summary,
    generate_key_takeaways,
    extract_important_terms,
)
from .learning_mode import explain_content


class RAGPipeline:
    """Retrieve document chunks and generate answers and insights."""

    def __init__(self, vector_store, user_id, document_id=None):
        self.retriever = Retriever(
            vector_store=vector_store,
            user_id=user_id,
            document_id=document_id,
        )
        self.llm = GeminiLLM()

    @staticmethod
    def _get_context(chunks):
        """Extract text from retrieved chunk metadata."""
        text_keys = ("text", "chunk_text", "content", "page_content")
        parts = []

        for chunk in chunks:
            if isinstance(chunk, str):
                text = chunk
            elif isinstance(chunk, dict):
                text = next(
                    (
                        chunk[key]
                        for key in text_keys
                        if isinstance(chunk.get(key), str)
                        and chunk[key].strip()
                    ),
                    None,
                )
            else:
                text = None

            if text:
                parts.append(text.strip())

        context = "\n\n".join(parts)

        if not context:
            raise ValueError(
                "Retrieved chunks contain no recognized text field."
            )

        return context

    def answer(self, question, top_k=5):
        """Answer a question using retrieved document chunks."""
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

        prompt = build_prompt(question, retrieved_chunks)
        return self.llm.generate(prompt)

    def insights(self, question, top_k=5):
        """Generate a summary, key takeaways, and important terms."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty")

        chunks = self.retriever.retrieve(question, top_k=top_k)

        if not chunks:
            return {
                "summary": "No relevant document content found.",
                "key_takeaways": "No relevant document content found.",
                "important_terms": "No relevant document content found.",
            }

        context = self._get_context(chunks)

        return {
            "summary": generate_summary(context, llm=self.llm),
            "key_takeaways": generate_key_takeaways(
                context, llm=self.llm
            ),
            "important_terms": extract_important_terms(
                context, llm=self.llm
            ),
        }

    def explain(self, question, level="student", top_k=5):
        """Explain retrieved content at the requested learning level."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty")

        chunks = self.retriever.retrieve(question, top_k=top_k)

        if not chunks:
            return "I could not find relevant content in the provided documents."

        context = self._get_context(chunks)

        return explain_content(
            context,
            level=level,
            llm=self.llm,
        )
