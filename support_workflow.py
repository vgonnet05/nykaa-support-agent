from grounded_generation import generate_grounded_answer
from order_lookup import check_order_status
from vector_store import fixed_collection


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
    """Route a support request to the relevant deterministic handler."""
    question_lower = question.lower()

    if record_id and any(
        word in question_lower
        for word in ("order", "track", "shipment", "status", "delivery")
    ):
        return {
            "type": "order",
            "result": handle_order_query(record_id),
        }

    return {
        "type": "policy",
        "result": handle_policy_query(question),
    }
