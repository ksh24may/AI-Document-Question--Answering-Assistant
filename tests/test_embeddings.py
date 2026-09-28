from document_processing.embeddings import generate_embedding


def test_generate_embedding():
    texts = ["This is a test document."]

    embeddings = generate_embedding(texts)

    assert len(embeddings) == 1
    assert len(embeddings[0]) > 0
