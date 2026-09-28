import faiss
import numpy as np


class VectorStore:
    def __init__(self, dimension):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata = []

    def add(self, embeddings, metadata):
        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        self.index.add(embeddings)
        self.metadata.extend(metadata)

    def search(self, query_embedding, top_k=5):
        query_embedding = np.asarray(
            query_embedding,
            dtype="float32"
        ).reshape(1, -1)

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for score, index in zip(scores[0], indices[0]):
            if index == -1:
                continue

            results.append({
                "score": float(score),
                **self.metadata[index]
            })

        return results


def create_metadata(chunks):
    metadata = []

    for chunk in chunks:
        metadata.append({
            "text": chunk["text"],
            "document": chunk["document"],
            "page": chunk["page"],
            "chunk_id": chunk["chunk_id"]
        })

    return metadata
