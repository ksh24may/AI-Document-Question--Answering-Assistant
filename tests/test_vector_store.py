import numpy as np

from document_processing.vector_store import VectorStore, create_metadata


def test_vector_store_add_and_search():
    store = VectorStore(dimension=3)

    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0]
    ])

    metadata = [
        {
            "text": "First document",
            "document": "sample.pdf",
            "page": 1,
            "chunk_id": "1_0"
        },
        {
            "text": "Second document",
            "document": "sample.pdf",
            "page": 2,
            "chunk_id": "2_0"
        }
    ]

    store.add(embeddings, metadata)

    results = store.search(
        np.array([1.0, 0.0, 0.0]),
        top_k=1
    )

    assert len(results) == 1
    assert results[0]["text"] == "First document"
    assert results[0]["document"] == "sample.pdf"


def test_create_metadata():
    chunks = [
        {
            "text": "Test chunk",
            "document": "sample.pdf",
            "page": 1,
            "chunk_id": "1_0"
        }
    ]

    metadata = create_metadata(chunks)

    assert len(metadata) == 1
    assert metadata[0]["text"] == "Test chunk"
    assert metadata[0]["document"] == "sample.pdf"
    assert metadata[0]["page"] == 1
    assert metadata[0]["chunk_id"] == "1_0"
