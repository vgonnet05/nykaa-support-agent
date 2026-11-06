from response_schema import SupportResponse


def test_support_response_schema():
    response = SupportResponse(
        answer="Please check the applicable return policy.",
        source_documents=["return_policy.txt"],
        requires_escalation=False,
    )
    assert response.answer
    assert response.source_documents == ["return_policy.txt"]
    assert response.requires_escalation is False


if __name__ == "__main__":
    test_support_response_schema()
    print("PASS: Structured SupportResponse schema")
