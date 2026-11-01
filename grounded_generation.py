
from vector_store import (
    sentence_collection,
    fixed_collection,
    search_policy,
)

SIMILARITY_THRESHOLD = 0.20

# In-memory cache and simple performance counters.
_answer_cache = {}
cache_hits = 0
cache_misses = 0


def generate_grounded_answer(query, collection):
    """Return a grounded answer, reusing cached results when available."""

    global cache_hits, cache_misses

    # Normalize the question and include the collection in the cache key.
    normalized_query = " ".join(query.lower().split())
    collection_name = getattr(collection, "name", str(id(collection)))
    cache_key = (collection_name, normalized_query)

    # Return the cached answer without repeating retrieval.
    if cache_key in _answer_cache:
        cache_hits += 1
        return _answer_cache[cache_key]

    cache_misses += 1

    results = search_policy(query, collection, k=3)

    if not results["documents"] or not results["documents"][0]:
        answer = "I don't know based on the available policy information."
    else:
        top_distance = results["distances"][0][0]
        top_similarity = 1 - top_distance

        if top_similarity < SIMILARITY_THRESHOLD:
            answer = "I don't know based on the available policy information."
        else:
            context = "\n".join(results["documents"][0])
            answer = (
                "Based on the available policy information:\n"
                f"{context}"
            )

    # Store the result for subsequent equivalent queries.
    _answer_cache[cache_key] = answer
    return answer


def get_cache_stats():
    """Return cache hit/miss statistics."""
    return {
        "cache_entries": len(_answer_cache),
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
    }


def clear_answer_cache():
    """Clear cached answers and reset counters."""
    global cache_hits, cache_misses
    _answer_cache.clear()
    cache_hits = 0
    cache_misses = 0


if __name__ == "__main__":
    for query in [
        "How can I get my money back?",
        "Which countries can Nykaa ship orders to internationally?",
        "Can I return a damaged product?",
        "What is the cancellation policy?",
        "How long does delivery take?",
        "What is the capital of France?",
        "How can I train my pet dog?",
    ]:
        print(f"\nQuestion: {query}")
        print(generate_grounded_answer(query, sentence_collection))
