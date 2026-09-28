from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def generate_embeddings(texts):
    """
    Generate embeddings for a list of text strings.
    """
    return model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
