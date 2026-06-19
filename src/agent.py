from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from config import TOP_K, MAX_RETRIES
from retrieval import retrieve as retrieve_chunks
from llm import answer, chat, decide_retrieve, grade_context, rewrite_query
from langfuse import observe

class State(TypedDict):
    question: str   # the original user question (never changes)
    query: str      # current search query (the agent may rewrite this)
    chunks: list    # retrieved chunks
    answer: str     # final answer
    tries: int      # how many times we've retrieved
    route: str      # triage decision: "retrieve" or "chat"
    steps: list     # human-readable log of what the agent did


# ---- nodes (state -> changed fields) ----

def triage_node(state: State) -> dict:
    if decide_retrieve(state["question"]):
        return {"route": "retrieve", "steps": state["steps"] + ["triage: needs the KB -> retrieve"]}
    return {"route": "chat", "steps": state["steps"] + ["triage: small talk -> answer directly"]}


def retrieve_node(state: State) -> dict:
    chunks = retrieve_chunks(state["query"], k=TOP_K)
    tries = state["tries"] + 1
    return {
        "chunks": chunks,
        "tries": tries,
        "steps": state["steps"] + [f"retrieve (try {tries}) query={state['query']!r}"],
    }


def rewrite_node(state: State) -> dict:
    new_query = rewrite_query(state["question"], state["chunks"])
    return {"query": new_query, "steps": state["steps"] + [f"context weak -> rewrite to {new_query!r}"]}


def generate_node(state: State) -> dict:
    return {"answer": answer(state["question"], state["chunks"]),
            "steps": state["steps"] + ["generate grounded answer"]}


def chat_node(state: State) -> dict:
    return {"answer": chat(state["question"]),
            "steps": state["steps"] + ["direct chat reply (no retrieval)"]}


# ---- conditional edges (state -> name of next node) ----

def route_from_triage(state: State) -> str:
    return state["route"]


def route_after_retrieve(state: State) -> str:
    if grade_context(state["question"], state["chunks"]):
        return "generate"                 # good enough -> answer
    if state["tries"] < MAX_RETRIES:
        return "rewrite"                  # weak, retries left -> try a better query
    return "generate"                     # out of retries -> generate will say "I don't have that"


# ---- build the graph ----

def build_agent():
    g = StateGraph(State)
    g.add_node("triage", triage_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("rewrite", rewrite_node)
    g.add_node("generate", generate_node)
    g.add_node("chat", chat_node)

    g.add_edge(START, "triage")
    g.add_conditional_edges("triage", route_from_triage, {"retrieve": "retrieve", "chat": "chat"})
    g.add_conditional_edges("retrieve", route_after_retrieve, {"generate": "generate", "rewrite": "rewrite"})
    g.add_edge("rewrite", "retrieve")     # the loop
    g.add_edge("generate", END)
    g.add_edge("chat", END)
    return g.compile()


_agent = build_agent()


@observe()
def run(question: str) -> dict:
    return _agent.invoke({
        "question": question,
        "query": question,
        "chunks": [],
        "answer": "",
        "tries": 0,
        "route": "",
        "steps": [],
    })