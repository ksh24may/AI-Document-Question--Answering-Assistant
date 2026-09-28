from .pdf_loader import extract_text_from_pdf
from .text_cleaner import clean_text
from .chunker import chunk_text


def process_pdf(file_path, chunk_size=1000, overlap=200):
    """
    Process a PDF into chunks with metadata.
    """

    pages = extract_text_from_pdf(file_path)

    all_chunks = []

    for page in pages:
        page_number = page["page"]
        raw_text = page["text"]

        cleaned_text = clean_text(raw_text)

        chunks = chunk_text(
            cleaned_text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for index, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "document": file_path,
                "page": page_number,
                "chunk_id": f"{page_number}_{index}"
            })

    return all_chunks