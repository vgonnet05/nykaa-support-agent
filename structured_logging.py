# Import tools for JSON Lines logging, timestamps, timing, and trace IDs.
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Reuse the existing PII masking function from Task 10.
from guardrails import mask_pii

# Store logs in a dedicated file in the project directory.
LOG_FILE = Path(__file__).parent / "logs" / "requests.jsonl"


def log_request(
    endpoint: str,
    request_text: str,
    start_time: float,
    status: str,
) -> str:
    """Write one structured JSONL entry for a request."""

    # Mask phone numbers before writing the request text to the log.
    safe_text = mask_pii(request_text)

    # Calculate request duration in milliseconds.
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # Build one structured log record.
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": str(uuid.uuid4()),
        "endpoint": endpoint,
        "request_text": safe_text,
        "duration_ms": duration_ms,
        "status": status,
    }

    # Create the log directory if it does not exist.
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Append one JSON object per line (JSON Lines format).
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry) + "\n")

    # Return the trace ID for debugging or correlation.
    return entry["trace_id"]