
from .llm import GeminiLLM


def _generate_insight(text, instruction, llm=None):
    """Generate an insight from supplied document text."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Document text cannot be empty")

    generator = llm if llm is not None else GeminiLLM()

    prompt = f"""
You are a document analysis assistant.
Use only the information provided below.
Do not invent facts.

Task:
{instruction}

Document content:
{text.strip()}
"""
    return generator.generate(prompt)


def generate_summary(text, llm=None):
    """Generate a concise summary of the document."""
    return _generate_insight(
        text,
        "Write a clear, concise summary of the document.",
        llm,
    )


def generate_key_takeaways(text, llm=None):
    """Generate the main takeaways as a readable list."""
    return _generate_insight(
        text,
        "List the most important key takeaways as bullet points.",
        llm,
    )


def extract_important_terms(text, llm=None):
    """Identify important terms and explain their meanings."""
    return _generate_insight(
        text,
        "Identify important terms and define each using the document context.",
        llm,
    )
