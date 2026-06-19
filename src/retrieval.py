from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from config import QDRANT_PATH, COLLECTION, EMBED_MODEL, TOP_K

# Load these once at import time (not per query) — the model is slow to construct.
_embedder = TextEmbedding(EMBED_MODEL)
_client = QdrantClient(path=QDRANT_PATH)


def retrieve(question: str, k: int = TOP_K) -> list[dict]:
    """Return the k most relevant chunks: [{text, source, score}]."""
    qvec = list(_embedder.embed([question]))[0].tolist()
    hits = _client.query_points(
        collection_name=COLLECTION,
        query=qvec,
        limit=k,
    ).points
    return [
        {"text": h.payload["text"], "source": h.payload["source"], "score": h.score}
        for h in hits
    ]