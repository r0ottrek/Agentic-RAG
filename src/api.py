from fastapi import FastAPI
from pydantic import BaseModel

from agent import run

app = FastAPI(title="Ask RootTrek")


class Query(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=Answer)
def chat(query: Query):
    result = run(query.question)
    sources = []
    for c in result["chunks"]:
        if c["source"] not in sources:
            sources.append(c["source"])
    return Answer(answer=result["answer"], sources=sources)