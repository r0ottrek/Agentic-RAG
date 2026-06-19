import os
import uuid
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import DATA_DIR, QDRANT_PATH, COLLECTION, EMBED_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
from chunking import chunk_text


def load_documents(data_dir: str) -> list[dict]:
    """Read every .md file in data_dir. Returns [{source, text}, ...]."""
    docs = []
    for name in os.listdir(data_dir):
        if name.endswith(".md"):
            path = os.path.join(data_dir, name)
            with open(path, "r", encoding="utf-8") as f:
                docs.append({"source": name, "text": f.read()})
    return docs


def main():
    docs = load_documents(DATA_DIR)
    print(f"Loaded {len(docs)} documents")

    # 1. Chunk every document, remembering which file each chunk came from.
    records = []  # [{source, text}]
    for d in docs:
        for piece in chunk_text(d["text"], CHUNK_SIZE, CHUNK_OVERLAP):
            records.append({"source": d["source"], "text": piece})
    print(f"Created {len(records)} chunks")

    # 2. Embed all chunks on CPU (first run downloads the model ~130MB).
    embedder = TextEmbedding(EMBED_MODEL)
    vectors = list(embedder.embed([r["text"] for r in records]))
    dim = len(vectors[0])
    print(f"Embedded {len(vectors)} chunks ({dim}-dim)")

    # 3. (Re)create the Qdrant collection and upsert the points.
    client = QdrantClient(path=QDRANT_PATH)
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec.tolist(),
            payload={"text": rec["text"], "source": rec["source"]},
        )
        for rec, vec in zip(records, vectors)
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    print(f"Stored {len(points)} points in collection '{COLLECTION}'")


if __name__ == "__main__":
    main()