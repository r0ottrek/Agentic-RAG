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
PERSONA = (
    "You are the assistant for RootTrek, the portfolio site of Ryder — a self-taught IT, "
    "security, and AI engineer who builds homelab, self-hosting, cybersecurity, and AI projects. "
    "You help visitors learn about Ryder's projects, blog posts, skills, and background. "
    "You're friendly, concise, and a little technical. You are NOT a general-knowledge bot "
    "(and definitely not about trees) — keep it about Ryder and his work."
)


def chat(question: str) -> str:
    """Direct reply when no retrieval is needed (greetings / 'what can you do')."""
    prompt = (
        f"{PERSONA}\n\n"
        "If the user is greeting you or asking what you do, briefly introduce yourself and invite "
        "them to ask about Ryder's projects, homelab, security work, or AI builds.\n\n"
        f"User: {question}"
    )
    return _client.models.generate_content(model=GEN_MODEL, contents=prompt).text



def decide_retrieve(question: str) -> bool:
    """YES if answering needs Ryder's notes/blog/projects; NO for small talk."""
    prompt = (
        "Does answering this question require looking up Ryder's notes, blog, or projects? "
        "Answer only YES or NO.\n\n"
        f"Question: {question}"
    )
    out = _client.models.generate_content(model=GEN_MODEL, contents=prompt).text
    return out.strip().lower().startswith("y")


def grade_context(question: str, chunks: list[dict]) -> bool:
    """YES if the retrieved chunks contain enough to answer the question."""
    context = "\n\n".join(c["text"] for c in chunks)
    prompt = (
        "Decide whether the CONTEXT contains enough information to answer the QUESTION. "
        "Answer only YES or NO.\n\n"
        f"QUESTION: {question}\n\nCONTEXT:\n{context}"
    )
    out = _client.models.generate_content(model=GEN_MODEL, contents=prompt).text
    return out.strip().lower().startswith("y")


def rewrite_query(question: str, chunks: list[dict]) -> str:
    """Produce a better search query when the first retrieval was weak."""
    weak = "\n\n".join(c["text"][:200] for c in chunks)
    prompt = (
        "The search results below were weak for the user's question. Write ONE improved search "
        "query (better keywords/phrasing) that would find better results. Return ONLY the query.\n\n"
        f"QUESTION: {question}\n\nWEAK RESULTS:\n{weak}"
    )
    return _client.models.generate_content(model=GEN_MODEL, contents=prompt).text.strip()