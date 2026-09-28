def build_prompt(question, retrieved_chunks):
    context = "\n\n".join(
        [
            f"Source: {chunk['document']}, Page: {chunk['page']}\n"
            f"{chunk['text']}"
            for chunk in retrieved_chunks
        ]
    )

    prompt = f"""
You are an AI document question-answering assistant.

Answer the user's question using only the provided document context.

If the answer cannot be found in the context, say:
"I could not find the answer in the provided documents."

Document context:
{context}

User question:
{question}

Answer:
"""

    return prompt.strip()