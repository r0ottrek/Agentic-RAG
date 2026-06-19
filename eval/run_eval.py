import sys
import os
import json
import time

sys.path.insert(0, "src")          # so we can import your agent from src/
from agent import run
from llm import generate


def _ask_judge(prompt: str) -> str:
    return generate(prompt)   # temperature=0 -> stable, comparable scores



def faithfulness(answer: str, contexts: list[str]) -> int:
    """1 if every claim in the answer is supported by the context, else 0."""
    ctx = "\n\n".join(contexts)
    out = _ask_judge(
        "Is every factual claim in the ANSWER supported by the CONTEXT? Answer only YES or NO.\n\n"
        f"CONTEXT:\n{ctx}\n\nANSWER:\n{answer}"
    )
    return 1 if out.strip().lower().startswith("y") else 0


def correctness(answer: str, ground_truth: str) -> int:
    """1-5: how well the answer matches the reference answer."""
    out = _ask_judge(
        "Compare the MODEL ANSWER to the REFERENCE. Score 1 (wrong) to 5 (fully correct) for how "
        "well it captures the key facts. Reply with ONLY the number.\n\n"
        f"REFERENCE:\n{ground_truth}\n\nMODEL ANSWER:\n{answer}"
    )
    for ch in out:
        if ch in "12345":
            return int(ch)
    return 0


def load_golden(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    golden = load_golden("eval/golden.jsonl")
    results = []

    for item in golden:
        out = run(item["question"])
        answer = out["answer"]
        contexts = [c["text"] for c in out["chunks"]]
        sources = [c["source"] for c in out["chunks"]]

        recall = 1 if item.get("expected_source") and item["expected_source"] in sources else 0
        faith = faithfulness(answer, contexts) if contexts else 1
        corr = correctness(answer, item["ground_truth"])

        results.append({"question": item["question"], "recall": recall,
                        "faithfulness": faith, "correctness": corr})
        print(f"[recall {recall} | faith {faith} | correct {corr}/5]  {item['question'][:55]}")
        time.sleep(1)  # be gentle on the free-tier rate limit

    n = len(results)
    avg_recall = sum(r["recall"] for r in results) / n
    avg_faith = sum(r["faithfulness"] for r in results) / n
    avg_corr = sum(r["correctness"] for r in results) / n / 5

    print("\n=== EVAL SUMMARY ===")
    print(f"Retrieval recall   : {avg_recall:.0%}")
    print(f"Faithfulness       : {avg_faith:.0%}")
    print(f"Answer correctness : {avg_corr:.0%}")

    os.makedirs("eval/results", exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = f"eval/results/{stamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"summary": {"recall": avg_recall, "faithfulness": avg_faith,
                               "correctness": avg_corr}, "items": results}, f, indent=2)
    print(f"\nSaved {path}")

    from langfuse import get_client
    get_client().flush()

if __name__ == "__main__":
    main()