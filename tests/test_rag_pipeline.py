
from unittest.mock import Mock

import pytest

from rag.pipeline import RAGPipeline


@pytest.fixture
def rag():
    # Avoid creating a real Gemini client or connecting to Pinecone.
    with (
        pytest.MonkeyPatch.context() as mp
    ):
        mp.setattr("rag.pipeline.GeminiLLM", lambda: Mock())
        mp.setattr(
            "rag.pipeline.Retriever",
            lambda **kwargs: Mock(),
        )

        pipeline = RAGPipeline(
            vector_store=Mock(),
            user_id="test-user",
        )

    pipeline.llm = Mock()
    pipeline.llm.generate.return_value = "Generated result"
    pipeline.retriever.retrieve.return_value = [
        {
            "text": "RAG retrieves relevant information and uses it to generate answers.",
            "page_number": 1,
            "document_name": "sample.pdf",
        }
    ]
    return pipeline


def test_insights_returns_all_three_sections(rag):
    result = rag.insights("What is RAG?")

    assert set(result) == {
        "summary",
        "key_takeaways",
        "important_terms",
    }
    assert all(value == "Generated result" for value in result.values())


def test_explain_uses_requested_learning_level(rag):
    result = rag.explain("What is RAG?", level="beginner")

    assert result == "Generated result"
    assert "Learning level: beginner" in rag.llm.generate.call_args.args[0]


def test_answer_still_works(rag):
    from rag import pipeline as pipeline_module

    pipeline_module.build_prompt = lambda question, chunks: "test prompt"

    assert rag.answer("What is RAG?") == "Generated result"
    rag.llm.generate.assert_called_with("test prompt")


def test_insights_handles_no_retrieved_chunks(rag):
    rag.retriever.retrieve.return_value = []

    result = rag.insights("What is RAG?")

    assert "No relevant" in result["summary"]


def test_explain_handles_no_retrieved_chunks(rag):
    rag.retriever.retrieve.return_value = []

    result = rag.explain("What is RAG?")

    assert "could not find" in result.lower()


@pytest.mark.parametrize("method", ["insights", "explain"])
def test_new_methods_reject_empty_questions(rag, method):
    with pytest.raises(ValueError):
        getattr(rag, method)("  ")
