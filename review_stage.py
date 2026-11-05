"""AutoGen two-agent review stage with deterministic, API-key-free mock clients."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator, Sequence

from pydantic import BaseModel

from mock_config import require_mock_llm

require_mock_llm()

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken
from autogen_core.models import (
    ChatCompletionClient,
    CreateResult,
    LLMMessage,
    ModelFamily,
    RequestUsage,
)


class Verdict(BaseModel):
    approved: bool
    final_answer: str
    reason: str


class DeterministicReviewClient(ChatCompletionClient):
    """Local mock model client with fixed outputs for the two review scenarios."""

    def __init__(self, role: str, scenario: str) -> None:
        super().__init__()
        self.role = role
        self.scenario = scenario
        self._usage = RequestUsage(prompt_tokens=0, completion_tokens=0)

    @property
    def model_info(self):
        return {
            "vision": False,
            "function_calling": False,
            "json_output": True,
            "family": ModelFamily.UNKNOWN,
            "structured_output": True,
            "multiple_system_messages": True,
        }

    @property
    def capabilities(self):
        return {
            "vision": False,
            "function_calling": False,
            "json_output": True,
        }

    def count_tokens(self, messages: Sequence[LLMMessage], **kwargs) -> int:
        return sum(len(str(message)) // 4 + 1 for message in messages)

    def remaining_tokens(self, messages: Sequence[LLMMessage], **kwargs) -> int:
        return max(0, 10000 - self.count_tokens(messages))

    def actual_usage(self) -> RequestUsage:
        return self._usage

    def total_usage(self) -> RequestUsage:
        return self._usage

    async def close(self) -> None:
        return None

    async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        cancellation_token: CancellationToken | None = None,
        **kwargs,
    ) -> CreateResult:
        if self.role == "reviewer":
            if self.scenario == "clean":
                content = (
                    "REVIEW: The draft is consistent with the supplied context. "
                    "No unsupported claims were identified. Recommend approval."
                )
            else:
                content = (
                    "REVIEW: The draft claims a universal 30-day return window, "
                    "which is not supported by the supplied context. Recommend revision."
                )
        elif self.scenario == "clean":
            content = json.dumps({
                "approved": True,
                "final_answer": (
                    "Return eligibility depends on the product and the applicable "
                    "Nykaa return policy. Check the product-specific terms."
                ),
                "reason": "The draft is consistent with the supplied context.",
            })
        else:
            content = json.dumps({
                "approved": False,
                "final_answer": (
                    "Return eligibility depends on the product and the applicable "
                    "Nykaa return policy. Check the product-specific terms or "
                    "contact customer support."
                ),
                "reason": (
                    "The original draft contained an unsupported universal "
                    "30-day claim; the revised answer removes it."
                ),
            })

        return CreateResult(
            finish_reason="stop",
            content=content,
            usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
            cached=False,
        )

    async def create_stream(
        self,
        messages: Sequence[LLMMessage],
        **kwargs,
    ) -> AsyncGenerator[str | CreateResult, None]:
        yield await self.create(messages, **kwargs)


def extract_verdict(result) -> Verdict:
    for message in result.messages:
        content = getattr(message, "content", None)
        if isinstance(content, Verdict):
            return content
        if isinstance(content, dict) and {"approved", "final_answer", "reason"} <= content.keys():
            return Verdict.model_validate(content)
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and {"approved", "final_answer", "reason"} <= parsed.keys():
                return Verdict.model_validate(parsed)
    raise AssertionError("No structured Verdict was returned by AutoGen.")


async def review_scenario(scenario: str):
    if scenario not in {"clean", "hallucination"}:
        raise ValueError("scenario must be 'clean' or 'hallucination'")

    reviewer = AssistantAgent(
        name="Reviewer",
        model_client=DeterministicReviewClient("reviewer", scenario),
        system_message=(
            "Review the composer draft against the supplied context. "
            "Identify unsupported claims and recommend approval or revision."
        ),
    )
    editor = AssistantAgent(
        name="FinalEditor",
        model_client=DeterministicReviewClient("editor", scenario),
        system_message=(
            "Return a structured verdict with approved, final_answer, and reason. "
            "Do not preserve unsupported claims."
        ),
        output_content_type=Verdict,
    )
    team = RoundRobinGroupChat(
        participants=[reviewer, editor],
        max_turns=2,
        custom_message_types=[StructuredMessage[Verdict]],
    )

    if scenario == "clean":
        draft = (
            "Return eligibility depends on the product and the applicable "
            "Nykaa return policy. Check the product-specific terms."
        )
    else:
        draft = "Every Nykaa product can be returned within 30 days, with no exceptions."

    result = await team.run(
        task=(
            f"Scenario: {scenario}\n"
            "Retrieved context: Return eligibility depends on the product "
            "and the applicable Nykaa return policy.\n"
            f"Composer draft: {draft}"
        )
    )
    verdict = extract_verdict(result)
    expected_approval = scenario == "clean"
    assert verdict.approved is expected_approval
    assert "applicable" in verdict.final_answer.lower()
    return result, verdict


async def run_review_demo() -> dict:
    clean_result, clean_verdict = await review_scenario("clean")
    hallucination_result, hallucination_verdict = await review_scenario("hallucination")

    transcript_parts = [
        "TASK 14 — AUTOGEN REVIEW TRANSCRIPTS",
        "Mode: deterministic MOCK_LLM; no external LLM API key.",
        "",
    ]
    for title, result, verdict in [
        ("CLEAN DRAFT — EXPECTED APPROVAL", clean_result, clean_verdict),
        ("PLANTED HALLUCINATION — EXPECTED REVISION", hallucination_result, hallucination_verdict),
    ]:
        transcript_parts.append(title)
        for message in result.messages:
            transcript_parts.append(f"[{message.source}]")
            transcript_parts.append(str(message.content))
        transcript_parts.extend([
            "Structured verdict:",
            verdict.model_dump_json(indent=2),
            "",
        ])

    transcript_parts.append("PASS: clean draft approved; unsupported draft rejected and revised.")
    transcript_dir = Path("transcripts")
    transcript_dir.mkdir(exist_ok=True)
    (transcript_dir / "task14_autogen_review.txt").write_text(
        "\n".join(transcript_parts) + "\n",
        encoding="utf-8",
    )

    return {
        "task": "Task 14 - AutoGen review",
        "mode": "MOCK_LLM",
        "external_llm_api_keys_required": False,
        "clean_draft": clean_verdict.model_dump(),
        "hallucination_draft": hallucination_verdict.model_dump(),
        "status": "PASS",
        "transcript": "transcripts/task14_autogen_review.txt",
    }


def main() -> None:
    evidence = asyncio.run(run_review_demo())
    print("AutoGen status:", evidence["status"])
    print("Clean draft approved:", evidence["clean_draft"]["approved"])
    print("Hallucination draft approved:", evidence["hallucination_draft"]["approved"])
    print("Transcript:", evidence["transcript"])


if __name__ == "__main__":
    main()
