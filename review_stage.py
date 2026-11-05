"""AutoGen review of the actual CrewAI draft using deterministic mock clients."""
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

from crew_agents import run_crew_demo


class Verdict(BaseModel):
    approved: bool
    final_answer: str
    reason: str


class DeterministicReviewClient(ChatCompletionClient):
    """Local mock model client; it never calls an external model provider."""

    def __init__(
        self,
        role: str,
        scenario: str,
        draft: str,
        revised_answer: str,
    ) -> None:
        super().__init__()
        self.role = role
        self.scenario = scenario
        self.draft = draft
        self.revised_answer = revised_answer
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
                    "REVIEW: The Composer draft is consistent with the retrieved "
                    "policy and order context. Recommend approval without changes."
                )
            else:
                content = (
                    "REVIEW: The draft contains an unsupported universal 30-day "
                    "return promise. The supplied context does not support that "
                    "claim. Recommend revision."
                )
        else:
            content = json.dumps({
                "approved": self.scenario == "clean",
                "final_answer": (
                    self.draft if self.scenario == "clean" else self.revised_answer
                ),
                "reason": (
                    "The actual CrewAI Composer draft is supported by the retrieved "
                    "context and is approved unchanged."
                    if self.scenario == "clean"
                    else (
                        "The deliberately injected 30-day promise was unsupported; "
                        "the final answer restores the original CrewAI draft."
                    )
                ),
            }, ensure_ascii=False)

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


async def review_scenario(
    scenario: str,
    customer_query: str,
    retrieved_context: str,
    crew_draft: str,
):
    if scenario not in {"clean", "hallucination"}:
        raise ValueError("scenario must be 'clean' or 'hallucination'")

    # The second scenario injects one deliberately unsupported statement
    # into the actual CrewAI draft so the reviewer has something to correct.
    submitted_draft = crew_draft
    if scenario == "hallucination":
        submitted_draft += (
            "\n\nUnsupported test claim: Every Nykaa product can be returned "
            "within 30 days, with no exceptions."
        )

    reviewer = AssistantAgent(
        name="PolicyComplianceReviewer",
        model_client=DeterministicReviewClient(
            "reviewer", scenario, submitted_draft, crew_draft
        ),
        system_message=(
            "Review the actual CrewAI Composer draft against the supplied "
            "retrieved context. Identify unsupported claims and recommend "
            "approval or revision."
        ),
    )
    editor = AssistantAgent(
        name="FinalEditor",
        model_client=DeterministicReviewClient(
            "editor", scenario, submitted_draft, crew_draft
        ),
        system_message=(
            "Return a structured verdict with approved, final_answer, and reason. "
            "Approve a supported draft unchanged. Remove unsupported claims."
        ),
        output_content_type=Verdict,
    )
    team = RoundRobinGroupChat(
        participants=[reviewer, editor],
        max_turns=2,
        custom_message_types=[StructuredMessage[Verdict]],
    )

    result = await team.run(
        task=(
            f"Scenario: {scenario}\n"
            f"Customer query: {customer_query}\n"
            "Original retrieved context from the CrewAI tools:\n"
            f"{retrieved_context}\n\n"
            "Actual CrewAI Composer draft under review:\n"
            f"{submitted_draft}"
        )
    )
    verdict = extract_verdict(result)

    if scenario == "clean":
        assert verdict.approved is True
        assert verdict.final_answer == crew_draft
    else:
        assert verdict.approved is False
        assert "30 days" in submitted_draft
        assert "30 days" not in verdict.final_answer
        assert verdict.final_answer == crew_draft

    return result, verdict, submitted_draft


async def run_review_demo() -> dict:
    # Use two actual CrewAI runs with distinct customer queries, not invented drafts.
    clean_crew_evidence = await asyncio.to_thread(
        run_crew_demo, "How long does an approved refund take?", "ORD1001"
    )
    revision_crew_evidence = await asyncio.to_thread(
        run_crew_demo, "What is the cancellation policy?", "ORD1002"
    )
    clean_draft = clean_crew_evidence["final_response"]
    revision_draft = revision_crew_evidence["final_response"]
    clean_context = json.dumps(
        clean_crew_evidence["tool_results"], indent=2, ensure_ascii=False
    )
    revision_context = json.dumps(
        revision_crew_evidence["tool_results"], indent=2, ensure_ascii=False
    )

    clean_result, clean_verdict, clean_submitted_draft = await review_scenario(
        "clean", "How long does an approved refund take?", clean_context, clean_draft
    )
    revision_result, revision_verdict, injected_draft = await review_scenario(
        "hallucination", "What is the cancellation policy?", revision_context, revision_draft
    )

    transcript_parts = [
        "TASK 14 — AUTOGEN REVIEW OF THE ACTUAL CREWAI DRAFT",
        "Mode: deterministic MOCK_LLM; no external LLM API key.",
        "",
        "CLEAN CASE — REFUND QUERY",
        "Customer query: How long does an approved refund take?",
        "Retrieved context passed to AutoGen:",
        clean_context,
        "Actual CrewAI Composer draft:",
        clean_draft,
        "CLEAN DRAFT — EXPECTED APPROVAL UNCHANGED",
        f"Submitted draft:\n{clean_submitted_draft}",
        "",
        "REVISION CASE — CANCELLATION QUERY",
        "Customer query: What is the cancellation policy?",
        "Retrieved context passed to AutoGen:",
        revision_context,
        "Actual CrewAI Composer draft:",
        revision_draft,
    ]
    for message in clean_result.messages:
        transcript_parts.append(f"[{message.source}]")
        transcript_parts.append(str(message.content))
    transcript_parts.extend([
        "Structured verdict:",
        clean_verdict.model_dump_json(indent=2),
        "",
        "PLANTED HALLUCINATION — EXPECTED REVISION",
        f"Submitted draft:\n{injected_draft}",
    ])
    for message in revision_result.messages:
        transcript_parts.append(f"[{message.source}]")
        transcript_parts.append(str(message.content))
    transcript_parts.extend([
        "Structured verdict:",
        revision_verdict.model_dump_json(indent=2),
        "",
        "PASS: actual CrewAI draft approved unchanged in scenario 1.",
        "PASS: unsupported 30-day promise removed in scenario 2.",
    ])

    transcript_dir = Path("transcripts")
    transcript_dir.mkdir(exist_ok=True)
    (transcript_dir / "task14_autogen_review.txt").write_text(
        "\n".join(transcript_parts) + "\n",
        encoding="utf-8",
    )

    evidence = {
        "task": "Task 14 - AutoGen review",
        "mode": "MOCK_LLM",
        "external_llm_api_keys_required": False,
        "crew_draft_used": True,
        "sample_queries": [
            "How long does an approved refund take?",
            "What is the cancellation policy?",
        ],
        "clean_draft": clean_verdict.model_dump(),
        "hallucination_draft": revision_verdict.model_dump(),
        "status": "PASS",
        "transcript": "transcripts/task14_autogen_review.txt",
    }
    Path("task14_review_evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return evidence


def main() -> None:
    evidence = asyncio.run(run_review_demo())
    print("AutoGen status:", evidence["status"])
    print("Actual CrewAI draft used:", evidence["crew_draft_used"])
    print("Clean draft approved unchanged:", evidence["clean_draft"]["approved"])
    print("Hallucination draft approved:", evidence["hallucination_draft"]["approved"])
    print("Transcript:", evidence["transcript"])


if __name__ == "__main__":
    main()
