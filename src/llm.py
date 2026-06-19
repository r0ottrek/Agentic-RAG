from google import genai
from config import GEMINI_API_KEY, GEN_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM = """You are a precise assistant answering questions about Ryder's homelab and projects.
Answer ONLY from the provided context. If the context doesn't contain the answer, say
"I don't have that in my notes." Cite the source filename(s) you used in square brackets."""


def answer(question: str, chunks: list[dict]) -> str:
    # Build a context block that includes each chunk's source so the model can cite it.
    context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)
    prompt = f"{SYSTEM}\n\nCONTEXT:\n{context}\n\nQUESTION: {question}\n\nANSWER:"
    resp = _client.models.generate_content(model=GEN_MODEL, contents=prompt)
    return resp.text