import sys
from agent import run


def main():
    question = " ".join(sys.argv[1:]) or input("Ask: ")
    result = run(question)

    print("\n--- AGENT STEPS ---")
    for s in result["steps"]:
        print(f"  - {s}")

    print("\n--- ANSWER ---")
    print(result["answer"])

    if result["chunks"]:
        print("\n--- SOURCES ---")
        seen = set()
        for c in result["chunks"]:
            if c["source"] not in seen:
                print(f"  {c['source']}")
                seen.add(c["source"])


if __name__ == "__main__":
    main()