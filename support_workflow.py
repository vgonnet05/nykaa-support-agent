# Import the existing grounded-generation function.
from grounded_generation import generate_grounded_answer

# Import the existing order lookup function.
from order_lookup import check_order_status

# Import the ChromaDB collection used for policy retrieval.
from vector_store import fixed_collection

# Import the input guardrail functions.
from guardrails import validate_input


def handle_policy_query(question: str) -> str:
    """Answer a policy question using retrieved knowledge-base content."""

    # Generate an answer grounded in retrieved policy information.
    return generate_grounded_answer(question, fixed_collection)


def handle_order_query(record_id: str) -> dict:
    """Return verified order details for the supplied order ID."""

    # Look up the order using the existing deterministic lookup.
    return check_order_status(record_id)


def handle_support_request(
    question: str,
    record_id: str | None = None
) -> dict:
    """Validate customer input before routing the support request."""

    # Mask PII and check for prompt-injection attempts.
    masked_question, is_injection = validate_input(question)

    # Block requests that match a known prompt-injection pattern.
    if is_injection:
        return {
            "type": "blocked",
            "result": "Your request could not be processed because it contains an unsafe instruction.",
        }

    # Use the masked question for all downstream processing.
    question_lower = masked_question.lower()

    # Route order-related questions to the order lookup handler.
    if record_id and any(
        word in question_lower
        for word in ("order", "track", "shipment", "status", "delivery")
    ):
        return {
            "type": "order",
            "result": handle_order_query(record_id),
        }

    # Route all other requests to the grounded policy handler.
    return {
        "type": "policy",
        "result": handle_policy_query(masked_question),
    }