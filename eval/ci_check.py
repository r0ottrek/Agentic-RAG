import sys
import os
import json
import glob
import uuid

sys.path.insert(0, "src")
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from chunking import chunk_text

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
FIXTURES_DIR = "eval/fixtures"
GOLDEN = "eval/fixtures_golden.jsonl"
TOP_K = 5
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
THRESHOLD = 0.80


def main():
    records = []
    for path in glob.glob(os.path.join(FIXTURES_DIR, "*.md")):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for piece in chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP):
            records.append({"source": os.path.basename(path), "text": piece})

    embedder = TextEmbedding(EMBED_MODEL)
    vectors = list(embedder.embed([r["text"] for r in records]))
    dim = len(vectors[0])
    client = QdrantClient(":memory:")
    client.create_collection("ci", vectors_config=VectorParams(size=dim, distance=Distance.COSINE))
    client.upsert("ci", [
        PointStruct(id=str(uuid.uuid4()), vector=v.tolist(), payload=r)
        for r, v in zip(records, vectors)
    ])

    golden = [json.loads(l) for l in open(GOLDEN, encoding="utf-8") if l.strip()]
    hits = 0
    for item in golden:
        qv = list(embedder.embed([item["question"]]))[0].tolist()
        found = [p.payload["source"] for p in client.query_points("ci", query=qv, limit=TOP_K).points]
        ok = item["expected_source"] in found
        hits += int(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {item['question'][:60]}")

    recall = hits / len(golden)
    print(f"\nRetrieval recall: {recall:.0%}  (threshold {THRESHOLD:.0%})")
    if recall < THRESHOLD:
        print("QUALITY GATE FAILED")
        sys.exit(1)
    print("QUALITY GATE PASSED")


if __name__ == "__main__":
    main()