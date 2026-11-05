import re


def mask_pii(text: str) -> str:
    """Mask supported Indian mobile numbers and explicitly labelled card suffixes."""
    phone_pattern = r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"
    masked_text = re.sub(
        phone_pattern,
        lambda match: "*" * len(match.group()),
        text,
    )

    # Match phrases such as "card ending in 1234" and
    # "credit card: 1234". Do not mask arbitrary four-digit numbers.
    card_suffix_pattern = (
        r"((?:(?:credit|debit|payment)\s+)?card\b[^\d]{0,30})(\d{4})\b"
    )
    return re.sub(
        card_suffix_pattern,
        lambda match: match.group(1) + "****",
        masked_text,
        flags=re.IGNORECASE,
    )


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"ignore\s+your\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
]


def detect_prompt_injection(text: str) -> bool:
    """Detect a limited set of known prompt-injection phrases."""
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in INJECTION_PATTERNS
    )


def validate_input(text: str) -> tuple[str, bool]:
    """Return PII-masked input and whether a known injection phrase was found."""
    masked_text = mask_pii(text)
    return masked_text, detect_prompt_injection(masked_text)
