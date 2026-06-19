from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEN_MODEL
from langfuse import observe

_client = genai.Client(api_key=GEMINI_API_KEY)

@observe(as_type="generation")
def generate(prompt: str, temperature: float = 0.0) -> str:
    """All model calls go through here. temperature=0 = deterministic (vital for eval)."""
    resp = _client.models.generate_content(
        model=GEN_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature),
    )
    return resp.text


SYSTEM = """You are a precise assistant answering questions about Ryder's homelab, projects, and blog.
Answer ONLY from the provided context. Be thorough and specific: include the relevant details,
names, numbers, and steps that appear in the context — not just a one-sentence summary. Do not add
anything that isn't supported by the context. If the context doesn't contain the answer, say
"I don't have that in my notes." Cite the source filename(s) you used in square brackets."""




def answer(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)
    prompt = f"{SYSTEM}\n\nCONTEXT:\n{context}\n\nQUESTION: {question}\n\nANSWER:"
    return generate(prompt)


PERSONA = (
    "You are the assistant for RootTrek, the portfolio site of Ryder — a self-taught IT, "
    "security, and AI engineer who builds homelab, self-hosting, cybersecurity, and AI projects. "
    "You help visitors learn about Ryder's projects, blog posts, skills, and background. "
    "You're friendly, concise, and a little technical. You are NOT a general-knowledge bot "
    "(and definitely not about trees) — keep it about Ryder and his work."
)


def chat(question: str) -> str:
    prompt = (
        f"{PERSONA}\n\n"
        "If the user is greeting you or asking what you do, briefly introduce yourself and invite "
        "them to ask about Ryder's projects, homelab, security work, or AI builds.\n\n"
        f"User: {question}"
    )
    return generate(prompt)


def decide_retrieve(question: str) -> bool:
    prompt = (
        "Does answering this question require looking up Ryder's notes, blog, or projects? "
        "Answer only YES or NO.\n\n"
        f"Question: {question}"
    )
    return generate(prompt).strip().lower().startswith("y")


def grade_context(question: str, chunks: list[dict]) -> bool:
    context = "\n\n".join(c["text"] for c in chunks)
    prompt = (
        "Decide whether the CONTEXT contains enough information to answer the QUESTION. "
        "Answer only YES or NO.\n\n"
        f"QUESTION: {question}\n\nCONTEXT:\n{context}"
    )
    return generate(prompt).strip().lower().startswith("y")


def rewrite_query(question: str, chunks: list[dict]) -> str:
    weak = "\n\n".join(c["text"][:200] for c in chunks)
    prompt = (
        "The search results below were weak for the user's question. Write ONE improved search "
        "query (better keywords/phrasing) that would find better results. Return ONLY the query.\n\n"
        f"QUESTION: {question}\n\nWEAK RESULTS:\n{weak}"
    )
    return generate(prompt).strip()
