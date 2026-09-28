from document_processing.embeddings import generate_embeddings


def test_generate_embeddings():
    texts = ["This is a test document."]

    embeddings = generate_embeddings(texts)

    assert len(embeddings) == 1
    assert len(embeddings[0]) > 0
