
from .llm import GeminiLLM


LEARNING_LEVELS = {
    "beginner": (
        "Explain in very simple language. "
        "Define unfamiliar words and use an easy example."
    ),
    "student": (
        "Give a student-friendly explanation with key concepts, "
        "relevant details, and an example where useful."
    ),
    "expert": (
        "Give a technically detailed explanation using precise "
        "terminology, assumptions, and relevant implications."
    ),
}


def explain_content(text, level="student", llm=None):
    """Explain document content at the requested learning level."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Document text cannot be empty")

    if not isinstance(level, str) or level.lower() not in LEARNING_LEVELS:
        raise ValueError(
            "Invalid level. Choose beginner, student, or expert."
        )

    generator = llm if llm is not None else GeminiLLM()
    instruction = LEARNING_LEVELS[level.lower()]

    prompt = f"""
You are a document-based learning assistant.
Explain only what is supported by the supplied content.
If information is missing, say so instead of inventing facts.

Learning level: {level.lower()}
Instructions: {instruction}

Document content:
{text.strip()}
"""
    return generator.generate(prompt)
