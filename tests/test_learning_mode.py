
import pytest

from rag.learning_mode import explain_content


class FakeLLM:
    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt):
        self.last_prompt = prompt
        return "Generated explanation"


@pytest.mark.parametrize(
    "level",
    ["beginner", "student", "expert"],
)
def test_explain_content_for_each_level(level):
    llm = FakeLLM()

    result = explain_content(
        "Machine learning learns patterns from data.",
        level=level,
        llm=llm,
    )

    assert result == "Generated explanation"
    assert f"Learning level: {level}" in llm.last_prompt
    assert "Machine learning learns patterns from data." in llm.last_prompt


def test_explain_content_defaults_to_student():
    llm = FakeLLM()

    explain_content("RAG retrieves context.", llm=llm)

    assert "Learning level: student" in llm.last_prompt


@pytest.mark.parametrize("level", ["advanced", "", None, 123])
def test_reject_invalid_learning_level(level):
    with pytest.raises(ValueError):
        explain_content("Some document content.", level=level, llm=FakeLLM())


def test_reject_empty_content():
    with pytest.raises(ValueError):
        explain_content("  ", llm=FakeLLM())
