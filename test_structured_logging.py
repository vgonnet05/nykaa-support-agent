import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import structured_logging


def test_jsonl_log_is_structured_and_masks_pii():
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "requests.jsonl"
        with patch.object(structured_logging, "LOG_FILE", target):
            trace_id = structured_logging.log_request(
                endpoint="/ask",
                request_text="Call me on 9876543210",
                start_time=time.perf_counter(),
                status="success",
            )

        record = json.loads(target.read_text(encoding="utf-8").strip())
        assert record["trace_id"] == trace_id
        assert record["endpoint"] == "/ask"
        assert record["status"] == "success"
        assert "9876543210" not in record["request_text"]
        assert record["duration_ms"] >= 0


if __name__ == "__main__":
    test_jsonl_log_is_structured_and_masks_pii()
    print("PASS: JSONL structured logging, trace ID and PII masking")
