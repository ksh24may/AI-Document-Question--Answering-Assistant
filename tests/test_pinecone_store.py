
from unittest.mock import MagicMock, patch

import pytest

from document_processing.pinecone_store import PineconeVectorStore


@pytest.fixture
def store():
    with patch(
        "document_processing.pinecone_store.Pinecone"
    ) as mock_pinecone:
        instance = PineconeVectorStore(
            api_key="test-key",
            index_name="test-index",
        )
        instance.index = MagicMock()
        yield instance


@patch(
    "document_processing.pinecone_store.generate_embeddings"
)
def test_index_chunks(mock_embeddings, store):
    mock_embeddings.return_value = [[0.1, 0.2, 0.3]]

    chunks = [
        {
            "text": "Pinecone stores vectors.",
            "document": "sample.pdf",
            "page": 1,
            "chunk_id": 0,
        }
    ]

    count = store.index_chunks(
        chunks, user_id="user-1", document_id="doc-1"
    )

    assert count == 1
    store.index.upsert.assert_called_once()
    vector = store.index.upsert.call_args.kwargs["vectors"][0]
    assert vector["metadata"]["user_id"] == "user-1"
    assert vector["metadata"]["document_id"] == "doc-1"


@patch(
    "document_processing.pinecone_store.generate_embeddings"
)
def test_search_filters_by_user(mock_embeddings, store):
    mock_embeddings.return_value = [[0.1, 0.2, 0.3]]

    match = MagicMock()
    match.score = 0.9
    match.metadata = {
        "user_id": "user-1",
        "document_id": "doc-1",
        "text": "Pinecone stores vectors.",
        "page": 1,
    }

    response = MagicMock()
    response.matches = [match]
    store.index.query.return_value = response

    results = store.search("What is Pinecone?", user_id="user-1")

    assert len(results) == 1
    assert results[0]["text"] == "Pinecone stores vectors."

    call = store.index.query.call_args.kwargs
    assert call["filter"] == {"user_id": {"$eq": "user-1"}}


def test_delete_document(store):
    store.delete_document("doc-1", "user-1")

    store.index.delete.assert_called_once_with(
        filter={
            "user_id": {"$eq": "user-1"},
            "document_id": {"$eq": "doc-1"},
        }
    )


def test_index_chunks_rejects_missing_user(store):
    with pytest.raises(ValueError):
        store.index_chunks(
            [{"text": "hello", "chunk_id": 0}],
            user_id="",
            document_id="doc-1",
        )


def test_search_rejects_empty_query(store):
    with pytest.raises(ValueError):
        store.search("", user_id="user-1")