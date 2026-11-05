"""Task 4: demonstrate grounded answers and the out-of-scope fallback."""
from grounded_generation import generate_grounded_answer
from vector_store import fixed_collection, search_policy


CASES = [
    ("How can I get my money back?", True),
    ("Which countries can Nykaa ship orders to internationally?", True),
    ("Can I return a damaged product?", True),
    ("What is the cancellation policy?", True),
    ("How long does delivery take?", True),
    ("What is the capital of France?", False),
    ("How can I train my pet dog?", False),
]


def main():
    if fixed_collection.count() == 0:
        raise RuntimeError("Build the ChromaDB collections with python vector_store.py first.")

    fallback = "I don't know based on the available policy information."
    passed = 0

    print("Task 4 — Grounded Answer Demonstration")
    print("Similarity = 1 - cosine distance; configured threshold = 0.20")

    for query, in_scope in CASES:
        results = search_policy(query, fixed_collection, k=3)
        top_distance = results["distances"][0][0]
        top_similarity = 1.0 - float(top_distance)
        answer = generate_grounded_answer(query, fixed_collection)
        accepted = fallback.lower() not in answer.lower()
        expected = in_scope
        status = "PASS" if accepted == expected else "FAIL"
        passed += status == "PASS"

        print("\nQuery:", query)
        print("Expected:", "in-scope" if in_scope else "out-of-scope")
        print(f"Top similarity: {top_similarity:.4f}")
        print("Expected source:", "grounded answer" if in_scope else "fallback")
        print("Actual:", "grounded answer" if accepted else "fallback")
        print(status)

        if status == "FAIL":
            raise AssertionError(f"Grounded-answer behavior failed for query: {query}")

    print(f"\nTask 4 result: {passed}/{len(CASES)} queries passed.")


if __name__ == "__main__":
    main()
