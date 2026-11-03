from unittest.mock import patch

import grounded_generation as gg


class FakeCollection:
    def __init__(self, name):
        self.name = name


def fake_search_policy(query, collection, k=3):
    return {
        "documents": [["Nykaa cancellation policy: orders can be cancelled before shipment."]],
        "distances": [[0.10]],
    }


def test_repeated_query_uses_cache():
    gg.clear_answer_cache()
    collection = FakeCollection("fixed_size_chunks")

    with patch.object(
        gg, "search_policy", side_effect=fake_search_policy
    ) as mocked_search:

        answer1 = gg.generate_grounded_answer(
            "What is the cancellation policy?", collection
        )

        answer2 = gg.generate_grounded_answer(
            "  WHAT IS THE CANCELLATION POLICY?  ", collection
        )

        assert answer1 == answer2
        assert mocked_search.call_count == 1

    stats = gg.get_cache_stats()
    assert stats["cache_misses"] == 1
    assert stats["cache_hits"] == 1
    assert stats["cache_entries"] == 1

    print("PASS: Normalized repeated query uses cache")
    print("Cache statistics:", stats)
    print("Retrieval calls:", mocked_search.call_count)


def test_different_collections_use_separate_cache_entries():
    gg.clear_answer_cache()

    collection1 = FakeCollection("fixed_size_chunks")
    collection2 = FakeCollection("sentence_chunks")

    with patch.object(
        gg, "search_policy", side_effect=fake_search_policy
    ) as mocked_search:

        gg.generate_grounded_answer(
            "What is the cancellation policy?", collection1
        )

        gg.generate_grounded_answer(
            "What is the cancellation policy?", collection2
        )

        assert mocked_search.call_count == 2

    stats = gg.get_cache_stats()
    assert stats["cache_misses"] == 2
    assert stats["cache_hits"] == 0
    assert stats["cache_entries"] == 2

    print("PASS: Different collections use separate cache entries")
    print("Cache statistics:", stats)
    print("Retrieval calls:", mocked_search.call_count)


if __name__ == "__main__":
    test_repeated_query_uses_cache()
    test_different_collections_use_separate_cache_entries()
    print("\nAll cache tests passed!")
