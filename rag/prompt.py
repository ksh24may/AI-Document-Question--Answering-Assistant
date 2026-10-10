
def build_prompt(question, retrieved_chunks):
    if not retrieved_chunks:
        return (
            "You are an AI document question-answering assistant.\n"
            "No relevant document context was retrieved.\n"
            "Answer: I could not find the answer in the provided documents."
        )

    context_parts = []

    for chunk in retrieved_chunks:
        document = chunk.get("document", "Unknown document")
        page = chunk.get("page", "Unknown")
        text = chunk.get("text", "")

        context_parts.append(
            f"Source: {document}, Page: {page}\n{text}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are an AI document question-answering assistant.

Answer the user's question using only the provided document context.

Rules:
1. Do not use outside information as evidence.
2. If the answer is not supported by the context, say:
   "I could not find the answer in the provided documents."
3. Cite the document name and page number for factual answers.
4. Use this citation format:
   Source: <document name>, Page: <page number>
5. Do not invent names, phone numbers, email addresses, marks, or other facts.
6. For questions asking for counts, percentages, or criteria,
   use only sufficient evidence from the provided context.
7. Clearly distinguish between confirmed information and information
   that cannot be determined from the retrieved context.

Document context:
{context}

User question:
{question}

Answer:
"""

    return prompt.strip()
