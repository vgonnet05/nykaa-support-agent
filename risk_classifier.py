
def classify_risk(text: str) -> str:
    """Classify a customer-support request as low, medium, or high risk."""

    text_lower = text.lower()

    high_risk_terms = [
        "fraud",
        "unauthorized payment",
        "money stolen",
        "account hacked",
        "legal action",
    ]

    medium_risk_terms = [
        "delayed",
        "refund",
        "complaint",
        "damaged",
        "escalation",
    ]

    if any(term in text_lower for term in high_risk_terms):
        return "high"

    if any(term in text_lower for term in medium_risk_terms):
        return "medium"

    return "low"
