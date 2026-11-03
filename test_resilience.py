from unittest.mock import patch
from support_workflow import handle_support_request

# Test 1: Policy retrieval failure
with patch(
    "support_workflow.handle_policy_query",
    side_effect=RuntimeError("internal database details"),
):
    response = handle_support_request(
        "What is the return policy?"
    )

    assert response["type"] == "policy"
    assert "temporarily unavailable" in response["result"]
    assert "internal database details" not in response["result"]

print("PASS: Policy failure fallback")


# Test 2: Order lookup failure
with patch(
    "support_workflow.handle_order_query",
    side_effect=RuntimeError("internal order system details"),
):
    response = handle_support_request(
        "Where is my order?",
        record_id="ORD1001",
    )

    assert response["type"] == "order"
    assert "error" in response["result"]
    assert "temporarily unavailable" in response["result"]["error"]
    assert "internal order system details" not in response["result"]["error"]

print("PASS: Order failure fallback")


print("\nAll resilience tests passed!")


# Test 3: Temporary retrieval failure followed by success
import grounded_generation

grounded_generation.clear_answer_cache()

mock_results = {
    "documents": [["Nykaa accepts returns under its return policy."]],
    "distances": [[0.1]],
}

with patch(
    "grounded_generation.search_policy",
    side_effect=[RuntimeError("Temporary failure"), mock_results],
) as mock_search, patch("grounded_generation.time.sleep"):

    answer = grounded_generation.generate_grounded_answer(
        "What is the return policy?",
        type("MockCollection", (), {"name": "test_collection"})(),
    )

    assert mock_search.call_count == 2
    assert "Nykaa accepts returns" in answer

print("PASS: Retrieval retry succeeds after temporary failure")


# Test 4: Persistent retrieval failure
grounded_generation.clear_answer_cache()

with patch(
    "grounded_generation.search_policy",
    side_effect=RuntimeError("Persistent failure"),
) as mock_search, patch("grounded_generation.time.sleep"):

    try:
        grounded_generation.generate_grounded_answer(
            "What is the cancellation policy?",
            type("MockCollection", (), {"name": "test_collection"})(),
        )
        raise AssertionError("Expected retrieval exception")
    except RuntimeError as error:
        assert str(error) == "Persistent failure"

    assert mock_search.call_count == 2

print("PASS: Persistent retrieval failure stops after two attempts")
