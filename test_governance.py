from support_workflow import handle_support_request


def test_high_risk_escalation():
    response = handle_support_request(
        "Someone made an unauthorized payment from my account."
    )
    assert response["type"] == "escalation"
    assert response["risk"] == "high"


def test_medium_risk_processing():
    response = handle_support_request("I want a refund.")
    assert response["type"] == "policy"
    assert response["risk"] == "medium"


def test_low_risk_processing():
    response = handle_support_request("What are your product categories?")
    assert response["type"] == "policy"
    assert response["risk"] == "low"


def test_runtime_limit_rejection_matches_api_contract():
    response = handle_support_request("oversized " * 5000)
    assert response["type"] == "rejected"
    assert isinstance(response["result"], str)
    assert "reason" not in response


if __name__ == "__main__":
    test_high_risk_escalation()
    print("PASS: High-risk escalation")
    test_medium_risk_processing()
    print("PASS: Medium-risk processing")
    test_low_risk_processing()
    print("PASS: Low-risk processing")
    test_runtime_limit_rejection_matches_api_contract()
    print("PASS: Runtime-limit rejection response contract")
    print("\nAll governance tests passed.")
