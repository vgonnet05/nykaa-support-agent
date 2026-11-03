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
