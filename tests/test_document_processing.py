from pathlib import Path

import pymupdf
import pytest

from document_processing import process_documents, process_pdf
from document_processing.chunker import chunk_text
from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_cleaner import clean_text


TEST_DATA = (
    Path(__file__).resolve().parent.parent
    / "test_data"
)

SAMPLE_1 = TEST_DATA / "sample.pdf"
SAMPLE_2 = TEST_DATA / "sample2.pdf"


def make_pdf(path, page_texts):
    """Create a test PDF."""

    document = pymupdf.open()

    for text in page_texts:

        page = document.new_page()

        if text:
            page.insert_textbox(
                pymupdf.Rect(
                    40, 40, 560, 800
                ),
                text,
                fontsize=8
            )

    document.save(path)
    document.close()

    return path


# -----------------------------
# TEXT CLEANER TESTS
# -----------------------------

def test_clean_text_collapses_whitespace():

    raw = (
        "Hello   \t world\r\n"
        "\r\n\r\n\r\n"
        "Next\u00a0line  "
    )

    assert clean_text(raw) == "Hello world\n\nNext line"


def test_clean_text_joins_hyphenated_words():

    assert (
        clean_text("infor-\nmation")
        == "information"
    )


def test_clean_text_empty():

    assert clean_text("   \n\n  ") == ""


# -----------------------------
# CHUNKER TESTS
# -----------------------------

def test_chunk_text_empty():

    assert chunk_text("") == []


def test_chunk_text_short_text():

    assert (
        chunk_text(
            "short text",
            chunk_size=100,
            overlap=10
        )
        == ["short text"]
    )


def test_chunk_text_respects_size():

    text = " ".join(
        f"word{i}"
        for i in range(500)
    )

    chunks = chunk_text(
        text,
        chunk_size=200,
        overlap=50
    )

    assert len(chunks) > 1

    assert all(
        len(chunk) <= 200
        for chunk in chunks
    )


def test_chunk_text_does_not_cut_words():

    text = " ".join(
        f"word{i}"
        for i in range(500)
    )

    original_words = set(text.split())

    chunks = chunk_text(
        text,
        chunk_size=200,
        overlap=50
    )

    for chunk in chunks:

        assert set(chunk.split()) <= original_words


def test_chunk_text_no_duplicate_tail():

    text = "x" * 1000

    assert (
        chunk_text(
            text,
            chunk_size=1000,
            overlap=200
        )
        == [text]
    )


@pytest.mark.parametrize(
    "size, overlap",
    [
        (0, 0),
        (100, 100),
        (100, 150),
        (100, -1)
    ]
)
def test_chunk_text_invalid_arguments(
    size,
    overlap
):

    with pytest.raises(ValueError):

        chunk_text(
            "some text",
            chunk_size=size,
            overlap=overlap
        )


# -----------------------------
# PDF LOADER TESTS
# -----------------------------

def test_extract_text_from_sample_pdf():

    pages = extract_text_from_pdf(
        SAMPLE_1
    )

    assert len(pages) == 1

    assert pages[0]["page"] == 1

    assert (
        "AI Document Question Answering Assistant"
        in pages[0]["text"]
    )


def test_extract_text_keeps_page_numbers(
    tmp_path
):

    pdf = make_pdf(
        tmp_path / "three.pdf",
        [
            "alpha page",
            "beta page",
            "gamma page"
        ]
    )

    pages = extract_text_from_pdf(pdf)

    assert [
        page["page"]
        for page in pages
    ] == [1, 2, 3]


def test_extract_missing_file_raises():

    with pytest.raises(FileNotFoundError):

        extract_text_from_pdf(
            "does_not_exist.pdf"
        )


def test_extract_non_pdf_raises(
    tmp_path
):

    txt = tmp_path / "notes.txt"

    txt.write_text(
        "not a pdf"
    )

    with pytest.raises(ValueError):

        extract_text_from_pdf(txt)


# -----------------------------
# PROCESSOR TESTS
# -----------------------------

REQUIRED_KEYS = {
    "text",
    "document",
    "page",
    "chunk_id"
}


def test_process_pdf_output_format():

    chunks = process_pdf(
        SAMPLE_1
    )

    assert len(chunks) > 0

    for chunk in chunks:

        assert (
            set(chunk.keys())
            == REQUIRED_KEYS
        )

        assert (
            isinstance(
                chunk["text"],
                str
            )
            and chunk["text"].strip()
        )

        assert (
            chunk["document"]
            == "sample.pdf"
        )

        assert (
            isinstance(
                chunk["page"],
                int
            )
            and chunk["page"] >= 1
        )

        assert isinstance(
            chunk["chunk_id"],
            str
        )


def test_process_multiple_documents():

    chunks = process_documents(
        [
            SAMPLE_1,
            SAMPLE_2
        ]
    )

    documents = {
        chunk["document"]
        for chunk in chunks
    }

    assert documents == {
        "sample.pdf",
        "sample2.pdf"
    }


def test_chunk_ids_are_unique():

    chunks = process_documents(
        [
            SAMPLE_1,
            SAMPLE_2
        ]
    )

    ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    assert len(ids) == len(set(ids))


def test_blank_pdf_gives_no_chunks(
    tmp_path
):

    pdf = make_pdf(
        tmp_path / "blank.pdf",
        [""]
    )

    assert process_pdf(pdf) == []


def test_process_documents_rejects_string():

    with pytest.raises(TypeError):

        process_documents(
            str(SAMPLE_1)
        )


def test_process_documents_empty_list():

    assert process_documents([]) == []