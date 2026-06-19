import sys
from retrieval import retrieve
from llm import answer


def main():
    question = " ".join(sys.argv[1:]) or input("Ask: ")
    chunks = retrieve(question)
    print("\n--- ANSWER ---")
    print(answer(question, chunks))
    print("\n--- SOURCES ---")
    for c in chunks:
        print(f"  {c['score']:.3f}  {c['source']}")


if __name__ == "__main__":
    main()