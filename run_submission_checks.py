"""Run the API-key-free capstone checks and save console transcripts."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
TRANSCRIPTS = ROOT / "transcripts"

COMMANDS = [
    ("task1_dataset", ["dataset.py"]),
    ("knowledge_base", ["create_knowledge_base.py"]),
    ("vector_store_build", ["vector_store.py"]),
    ("retrieval_evaluation", ["evaluate_retrieval.py"]),
    ("quality_evaluation", ["evaluate_quality.py"]),
    ("guardrails", ["test_guardrails.py"]),
    ("conversation_memory", ["test_conversation_memory.py"]),
    ("response_schema", ["test_response_schema.py"]),
    ("governance", ["test_governance.py"]),
    ("least_autonomy", ["test_least_autonomy.py"]),
    ("runtime_resilience", ["test_resilience.py"]),
    ("answer_cache", ["test_cache.py"]),
    ("api_contract", ["test_api_contract.py"]),
    ("structured_logging", ["test_structured_logging.py"]),
    ("websocket", ["test_websocket.py"]),
    ("websocket_disconnect", ["test_websocket_disconnect.py"]),
    ("task7_crewai", ["crew_agents.py"]),
    ("task14_autogen", ["review_stage.py"]),
]


def main() -> int:
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    child_env = os.environ.copy()
    child_env["MOCK_LLM"] = "true"
    child_env["CREWAI_DISABLE_TELEMETRY"] = "true"
    child_env["OTEL_SDK_DISABLED"] = "true"

    # Prove the examples do not depend on common provider credentials.
    for key in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GROQ_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "MISTRAL_API_KEY",
        "COHERE_API_KEY",
        "TOGETHER_API_KEY",
        "FIREWORKS_API_KEY",
        "DEEPSEEK_API_KEY",
        "XAI_API_KEY",
        "HUGGINGFACEHUB_API_TOKEN",
        "HF_TOKEN",
    ):
        child_env.pop(key, None)
    for key in list(child_env):
        if key.endswith("_API_KEY"):
            child_env.pop(key, None)

    results = []
    for name, args in COMMANDS:
        command = [sys.executable, *args]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=child_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        transcript_path = TRANSCRIPTS / f"run_{name}.txt"
        transcript_path.write_text(
            f"$ {' '.join(command)}\n"
            f"exit_code={completed.returncode}\n\n"
            f"{completed.stdout}",
            encoding="utf-8",
        )
        status = "PASS" if completed.returncode == 0 else "FAIL"
        results.append((name, status, completed.returncode, transcript_path.name))
        print(f"{status}: {name} (exit {completed.returncode})")
        if completed.returncode != 0:
            print(completed.stdout[-4000:])

    lines = [
        "# Submission check summary",
        "",
        "Mode: MOCK_LLM=true; common external LLM API-key variables removed from child processes.",
        "",
        "| Check | Status | Exit code | Transcript |",
        "|---|---:|---:|---|",
    ]
    for name, status, code, transcript in results:
        lines.append(f"| {name} | {status} | {code} | [{transcript}]({transcript}) |")
    failed = [item for item in results if item[1] != "PASS"]
    lines.extend([
        "",
        f"Result: {'FAIL' if failed else 'PASS'} — {len(results) - len(failed)}/{len(results)} commands passed.",
        "",
        "Initial setup may require internet access to download the local Sentence Transformers embedding model. No LLM API key is used.",
    ])
    (TRANSCRIPTS / "submission_check_summary.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"\nSummary: {TRANSCRIPTS / 'submission_check_summary.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
