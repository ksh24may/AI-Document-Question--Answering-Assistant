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

Rules:
1. Do not use information outside the provided context.
2. If the answer cannot be found in the context, say:
   "I could not find the answer in the provided documents."
3. After the answer, provide the sources used.
4. For every source, include the document name and page number.
5. Use this citation format:
   Source: <document name>, Page: <page number>

Document context:
{context}

User question:
{question}

Answer:
"""

    return prompt.strip()