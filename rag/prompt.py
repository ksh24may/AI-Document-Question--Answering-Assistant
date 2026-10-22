
def format_context(retrieved_chunks):
    """Format retrieved document chunks with their source details."""
    formatted_chunks = []

    for chunk in retrieved_chunks:
        document = chunk.get("document", "Unknown document")
        page = chunk.get("page", "Unknown page")
        text = chunk.get("text", "")

        formatted_chunks.append(
            f"Source: {document}, Page: {page}\n{text}"
        )

    return "\n\n".join(formatted_chunks)


def build_prompt(question, retrieved_chunks, learning_level="student"):
    """Build a document-grounded answer prompt for the selected level."""

    learning_instructions = {
        "beginner": (
            "Explain the answer in very simple language. "
            "Assume the reader is new to the topic. "
            "Use short sentences and explain technical terms. "
            "Use simple examples only when supported by the context."
        ),
        "student": (
            "Explain the answer clearly at a college-student level. "
            "Include relevant concepts, details, and examples "
            "supported by the document."
        ),
        "expert": (
            "Give a precise, technical, and detailed explanation. "
            "Use relevant terminology and discuss technical details "
            "supported by the document."
        ),
    }

    instructions = learning_instructions.get(
        learning_level,
        learning_instructions["student"]
    )

    context = format_context(retrieved_chunks)

    return f"""
You are an AI document question-answering assistant.

Answer the user's question using only the provided document context.

Rules:
1. Do not invent facts or use unsupported external information.
2. If the answer is not available in the context, clearly say:
   "I could not find the answer in the provided documents."
3. Follow the selected learning-level instructions.
4. Refer to relevant document names and page numbers when possible.
5. If the context only partially answers the question, explain what
   is supported and identify what could not be found.

Learning level: {learning_level}

Learning-level instructions:
{instructions}

Document context:
{context}

User question:
{question}

Answer:
""".strip()


def build_insights_prompt(retrieved_chunks):
    """Build a prompt that requests structured document insights."""

    context = format_context(retrieved_chunks)

    return f"""
You are an AI document analysis assistant.

Analyze only the document excerpts provided below.
Do not invent facts, results, statistics, or conclusions.

Return ONLY a valid JSON object. Do not include Markdown
code fences or introductory text.

Use exactly this structure:
{{
  "summary": "A concise summary of the document excerpts",
  "key_takeaways": [
    "Important point 1",
    "Important point 2"
  ],
  "important_terms": [
    {{
      "term": "Term name",
      "definition": "A clear explanation of the term"
    }}
  ],
  "major_findings": [
    "Finding supported by the document"
  ]
}}

Requirements:
1. The summary must reflect the provided excerpts.
2. Key takeaways must contain important points supported by the text.
3. Explain technical terms clearly and accurately.
4. Major findings must only include conclusions supported by the excerpts.
5. Use empty arrays when a section has no supported information.
6. Do not fabricate document names, page numbers, or citations.
7. Keep the JSON valid and ensure all strings use proper JSON escaping.

Document excerpts:
{context}
""".strip()
