from pathlib import Path


def create_metadata(document_path, page_number, chunk_id):
    """
    Create metadata for a document chunk.
    """

    return {
        "document": Path(document_path).name,
        "page": page_number,
        "chunk_id": chunk_id
    }