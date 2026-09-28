from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_cleaner import clean_text
from document_processing.chunker import chunk_text
from document_processing.processor import process_pdf


def test_clean_text():
    text = "Hello    world\n\n\nThis is a test."

    result = clean_text(text)

    assert result == "Hello world\n\nThis is a test."


def test_chunk_text():
    text = "a" * 2500

    chunks = chunk_text(
        text,
        chunk_size=1000,
        overlap=200
    )

    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)


def test_pdf_extraction():
    pages = extract_text_from_pdf("test_data/sample.pdf")

    assert len(pages) > 0
    assert pages[0]["page"] == 1
    assert "AI Document Question Answering Assistant" in pages[0]["text"]


def test_process_pdf():
    chunks = process_pdf("test_data/sample.pdf")

    assert len(chunks) > 0

    first_chunk = chunks[0]

    assert "text" in first_chunk
    assert "document" in first_chunk
    assert "page" in first_chunk
    assert "chunk_id" in first_chunk