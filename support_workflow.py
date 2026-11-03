from grounded_generation import generate_grounded_answer
from order_lookup import check_order_status
from vector_store import fixed_collection
from guardrails import validate_input
from risk_classifier import classify_risk
from runtime_limits import check_runtime_limits


def handle_policy_query(question: str) -> str:
    """Answer a policy question using retrieved knowledge-base content."""
    return generate_grounded_answer(question, fixed_collection)


def handle_order_query(record_id: str) -> dict:
    """Return verified order details for the supplied order ID."""
    return check_order_status(record_id)


def handle_support_request(
    question: str,
    record_id: str | None = None
) -> dict:
    """Validate, limit, classify, and safely route a support request."""

    limits = check_runtime_limits(question)

    if not limits["allowed"]:
        return {
            "type": "rejected",
            "reason": limits["reason"],
        }

    masked_question, is_injection = validate_input(question)

    if is_injection:
        return {
            "type": "blocked",
            "result": (
                "Your request could not be processed because "
                "it contains an unsafe instruction."
            ),
        }

    risk_level = classify_risk(masked_question)
    question_lower = masked_question.lower()

    # Governance: escalate high-risk requests for human review.
    if risk_level == "high":
        return {
            "type": "escalation",
            "risk": "high",
            "result": (
                "Your request requires additional review by our "
                "customer support team. Please contact customer support."
            ),
        }

    if record_id and any(
        word in question_lower
        for word in ("order", "track", "shipment", "status", "delivery")
    ):
        try:
            result = handle_order_query(record_id)
            return {
                "type": "order",
                "risk": risk_level,
                "result": result,
            }
        except Exception:
            return {
                "type": "order",
                "risk": risk_level,
                "result": {
                    "error": "Order service is temporarily unavailable. Please try again later."
                },
            }

    try:
        result = handle_policy_query(masked_question)
        return {
            "type": "policy",
            "risk": risk_level,
            "result": result,
        }
    except Exception:
        return {
            "type": "policy",
            "risk": risk_level,
            "result": (
                "Policy information is temporarily unavailable. "
                "Please try again later."
            ),
        }
