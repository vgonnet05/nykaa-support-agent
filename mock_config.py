"""Shared configuration for deterministic, API-key-free capstone demos."""
import os


def mock_llm_enabled() -> bool:
    value = os.getenv("MOCK_LLM", "true").strip().lower()
    return value in {"1", "true", "yes", "on"}


def require_mock_llm() -> None:
    """Fail closed if a demo is explicitly launched outside mock mode."""
    if not mock_llm_enabled():
        raise RuntimeError(
            "This capstone demo is designed for MOCK_LLM=true. "
            "Set MOCK_LLM=true; no external LLM provider is configured."
        )
