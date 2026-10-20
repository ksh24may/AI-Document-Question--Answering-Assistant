
import pytest

from rag.insights import (
    generate_summary,
    generate_key_takeaways,
    extract_important_terms,
)


class FakeLLM:
    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt):
        self.last_prompt = prompt
        return "Generated test result"


def test_generate_summary():
    llm = FakeLLM()
    result = generate_summary("RAG combines retrieval and generation.", llm)

    assert result == "Generated test result"
    assert "summary" in llm.last_prompt.lower()
    assert "RAG combines retrieval and generation." in llm.last_prompt


def test_generate_key_takeaways():
    llm = FakeLLM()
    result = generate_key_takeaways("RAG retrieves relevant documents.", llm)

    assert result == "Generated test result"
    assert "takeaways" in llm.last_prompt.lower()


def test_extract_important_terms():
    llm = FakeLLM()
    result = extract_important_terms("Embeddings represent text as vectors.", llm)

    assert result == "Generated test result"
    assert "terms" in llm.last_prompt.lower()


@pytest.mark.parametrize(
    "function",
    [
        generate_summary,
        generate_key_takeaways,
        extract_important_terms,
    ],
)
def test_insights_reject_empty_text(function):
    with pytest.raises(ValueError):
        function("   ", llm=FakeLLM())
