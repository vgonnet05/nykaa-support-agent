# Import Python's regular expression module.
# We use it to find phone numbers inside customer messages.
import re


def mask_pii(text: str) -> str:
    """
    Mask Indian mobile numbers in customer messages.

    Examples:
        9876543210      -> **********
        +91 9876543210  -> **************
    """

    # Match a 10-digit Indian mobile number.
    # The +91 country code is optional.
    # The lookarounds prevent matching part of a longer number.
    pattern = r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"

    # Replace each detected phone number with asterisks.
    # Keep the same number of characters as the original match.
    masked_text = re.sub(
        pattern,
        lambda match: "*" * len(match.group()),
        text,
    )

    # Return the message with phone numbers masked.
    return masked_text

# Define phrases commonly associated with prompt-injection attempts.
# This is a basic keyword-based guardrail, not a complete detector.
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"ignore\s+your\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
]


def detect_prompt_injection(text: str) -> bool:
    """
    Return True when the message matches a known injection pattern.
    Return False when no pattern matches.
    """

    # Check the message against each known injection pattern.
    for pattern in INJECTION_PATTERNS:

        # Ignore differences between uppercase and lowercase letters.
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # No known injection phrase was detected.
    return False

def validate_input(text: str) -> tuple[str, bool]:
    """
    Mask PII and check for prompt injection.

    Returns:
        masked_text: The input with phone numbers masked.
        is_injection: True if a known injection pattern is detected.
    """

    # Mask personal information before further processing or logging.
    masked_text = mask_pii(text)

    # Check the masked message for known prompt-injection patterns.
    is_injection = detect_prompt_injection(masked_text)

    # Return the safe-to-process text and the detection result.
    return masked_text, is_injection