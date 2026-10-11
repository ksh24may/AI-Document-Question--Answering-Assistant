from pathlib import Path

from .pdf_loader import extract_text_from_pdf
from .text_cleaner import clean_text
from .chunker import chunk_text
from .metadata import create_metadata


def process_pdf(file_path, chunk_size=1000, overlap=200):
    """
    Process one PDF into chunks with metadata.
    """

    document_name = Path(file_path).name

    pages = extract_text_from_pdf(file_path)

    all_chunks = []

    for page in pages:
        page_number = page["page"]

        cleaned_text = clean_text(page["text"])

        chunks = chunk_text(
            cleaned_text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for index, chunk in enumerate(chunks):

            # Unique ID for each document/page/chunk
            chunk_id = f"{document_name}_p{page_number}_c{index}"

            metadata = create_metadata(
                file_path,
                page_number,
                chunk_id
            )

            all_chunks.append({
                "text": chunk,
                **metadata
            })

    return all_chunks


def process_documents(file_paths, chunk_size=1000, overlap=200):
    """
    Process multiple PDF documents.
    """

    # Prevent accidentally passing one string instead of a list
    if isinstance(file_paths, (str, Path)):
        raise TypeError(
            "file_paths must be a list of paths, "
            "for example ['a.pdf', 'b.pdf']"
        )

    # Check duplicate file names
    names = [Path(path).name for path in file_paths]

    duplicates = sorted({
        name for name in names
        if names.count(name) > 1
    })

    if duplicates:
        raise ValueError(
            f"Two or more PDFs have the same file name: {duplicates}"
        )

    all_chunks = []

    for file_path in file_paths:

        chunks = process_pdf(
            file_path,
            chunk_size=chunk_size,
            overlap=overlap
        )

        all_chunks.extend(chunks)

    return all_chunks