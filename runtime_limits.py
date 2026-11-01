
# Configurable request limits
MAX_INPUT_TOKENS = 2_000
MAX_OUTPUT_TOKENS = 500
MAX_REQUEST_COST = 0.20  # Illustrative cost cap

# Illustrative prices per million tokens
INPUT_COST_PER_MILLION = 100
OUTPUT_COST_PER_MILLION = 250


def estimate_tokens(text: str) -> int:
    """Rough token estimate; not an exact model tokenizer."""
    return (len(text) + 3) // 4


def check_runtime_limits(question: str) -> dict:
    """Check estimated input/output tokens and total request cost."""

    input_tokens = estimate_tokens(question)

    if input_tokens > MAX_INPUT_TOKENS:
        return {
            "allowed": False,
            "reason": "Input token limit exceeded",
            "estimated_input_tokens": input_tokens,
        }

    estimated_cost = (
        input_tokens * INPUT_COST_PER_MILLION
        + MAX_OUTPUT_TOKENS * OUTPUT_COST_PER_MILLION
    ) / 1_000_000

    if estimated_cost > MAX_REQUEST_COST:
        return {
            "allowed": False,
            "reason": "Estimated request cost limit exceeded",
            "estimated_input_tokens": input_tokens,
            "estimated_output_tokens": MAX_OUTPUT_TOKENS,
            "estimated_cost": round(estimated_cost, 6),
        }

    return {
        "allowed": True,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": MAX_OUTPUT_TOKENS,
        "estimated_cost": round(estimated_cost, 6),
    }
