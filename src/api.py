from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agent import run

limiter = Limiter(key_func=get_remote_address)          # rate-limit per client IP

app = FastAPI(title="Ask RootTrek")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Only browsers on your site (and local dev) may call this:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://roottrek.org", "https://www.roottrek.org", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Query(BaseModel):
    question: str = Field(min_length=1, max_length=500)   # input cap


class Answer(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=Answer)
@limiter.limit("10/minute")
def chat(request: Request, query: Query):
    result = run(query.question)
    sources = []
    for c in result["chunks"]:
        if c["source"] not in sources:
            sources.append(c["source"])
    return Answer(answer=result["answer"], sources=sources)