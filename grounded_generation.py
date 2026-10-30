# Import the two ChromaDB collections and helper functions from vector_store.py.
from vector_store import (
    sentence_collection,
    fixed_collection,
    search_policy,
)

# Similarity threshold established from our earlier retrieval experiments.
# Queries below this threshold should trigger the fallback response.
SIMILARITY_THRESHOLD = 0.20


def generate_grounded_answer(query, collection):
    """
    Generate an answer using retrieved knowledge-base chunks.

    Args:
        query: The customer's question.
        collection: The ChromaDB collection to search.

    Returns:
        A policy-based answer or an 'I don't know' fallback.
    """

    # Step 1: Retrieve the three most relevant policy chunks.
    # search_policy() returns the matching documents, distances, and metadata.
    results = search_policy(query, collection, k=3)

    # Step 2: Check whether ChromaDB returned any documents.
    # If nothing was retrieved, we cannot safely answer the question.
    if not results["documents"] or not results["documents"][0]:
        return "I don't know based on the available policy information."

    # Step 3: Get the distance of the highest-ranked chunk.
    # ChromaDB's cosine distance is converted to cosine similarity.
    # Similarity = 1 - cosine distance.
    top_distance = results["distances"][0][0]
    top_similarity = 1 - top_distance

    # Step 4: Reject questions when the best matching chunk
    # does not meet our experimentally chosen similarity threshold.
    if top_similarity < SIMILARITY_THRESHOLD:
        return "I don't know based on the available policy information."

    # Step 5: Combine the retrieved chunks into a single context.
    # This context contains the policy information used for the answer.
    context = "\n".join(results["documents"][0])

    # Step 6: Return the retrieved policy text as the answer.
    # Under MOCK_LLM, this provides a deterministic baseline without
    # inventing facts or requiring an external language-model API.
    return f"Based on the available policy information:\n{context}"


# Run the following examples only when this file is executed directly.
# Importing this module from another file will not run these tests.
if __name__ == "__main__":

    # Five in-scope questions and one out-of-scope question.
    test_queries = [
        "How can I get my money back?",
        "Which countries can Nykaa ship orders to internationally?",
        "Can I return a damaged product?",
        "What is the cancellation policy?",
        "How long does delivery take?",
        "What is the capital of France?",
        "How can I train my pet dog?",
    ]

    # Run every question against the sentence-based collection.
    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Question: {query}")

        # Retrieve context and generate a grounded response.
        answer = generate_grounded_answer(query, sentence_collection)
        print(f"Answer: {answer}")