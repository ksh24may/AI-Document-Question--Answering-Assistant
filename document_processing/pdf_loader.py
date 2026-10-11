from pathlib import Path

import pymupdf


def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF page by page.
    """

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"PDF not found: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Not a PDF file: {path}"
        )

    pages = []

    with pymupdf.open(path) as document:

        for page_number, page in enumerate(
            document,
            start=1
        ):

            pages.append({
                "page": page_number,
                "text": page.get_text()
            })

    return pages