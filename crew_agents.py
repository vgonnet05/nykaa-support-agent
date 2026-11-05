"""Three-agent CrewAI demonstration using deterministic local tools and a mock LLM."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import re

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM
from crewai.tools import tool

from grounded_generation import generate_grounded_answer
from mock_config import require_mock_llm
from order_lookup import check_order_status
from vector_store import build_collections, fixed_collection

require_mock_llm()

ACTUAL_TOOL_CALLS: list[dict] = []
TOOL_RESULTS: dict[str, object] = {}


@tool("rag_policy_search")
def rag_policy_search(query: str) -> str:
    """Retrieve policy evidence from the local ChromaDB knowledge base."""
    result = generate_grounded_answer(query, fixed_collection)
    TOOL_RESULTS["rag_policy_search"] = result
    ACTUAL_TOOL_CALLS.append({"tool": "rag_policy_search", "input": query})
    return result


@tool("check_order_status")
def order_status_tool(record_id: str) -> str:
    """Look up a synthetic order by its record ID."""
    result = check_order_status(record_id)
    TOOL_RESULTS["check_order_status"] = result
    ACTUAL_TOOL_CALLS.append({"tool": "check_order_status", "input": record_id})
    return json.dumps(result, ensure_ascii=False)


class DeterministicCrewMockLLM(BaseLLM):
    """CrewAI BaseLLM implementation; never calls an external model provider."""

    def __init__(self) -> None:
        super().__init__(model="nykaa-deterministic-mock")
        self.calls: dict[str, int] = {}

    def call(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        from_task=None,
        from_agent=None,
        response_model=None,
    ) -> str:
        role = getattr(from_agent, "role", "")
        task_description = getattr(from_task, "description", "")
        call_number = self.calls.get(role, 0)
        self.calls[role] = call_number + 1

        if "Composer" in role:
            rag = TOOL_RESULTS.get("rag_policy_search", "")
            order = TOOL_RESULTS.get("check_order_status", {})
            if not rag or not order:
                return "Final Answer: ERROR — required specialist tool results are missing."
            return (
                "Final Answer:\n"
                "Policy evidence:\n"
                f"{rag}\n\n"
                "Order lookup:\n"
                f"{json.dumps(order, ensure_ascii=False)}"
            )

        if "Retrieval" in role and call_number == 0:
            match = re.search(r"Customer question:\s*(.+)", task_description)
            query = match.group(1).strip() if match else "What is the refund policy?"
            return (
                "Thought: Retrieve policy evidence.\n"
                "Action: rag_policy_search\n"
                f"Action Input: {json.dumps({'query': query})}"
            )

        if "Lookup" in role and call_number == 0:
            match = re.search(r"Order ID:\s*([A-Za-z0-9_-]+)", task_description)
            record_id = match.group(1) if match else "ORD1001"
            return (
                "Thought: Look up the order record.\n"
                "Action: check_order_status\n"
                f"Action Input: {json.dumps({'record_id': record_id})}"
            )

        return "Final Answer: The requested tool operation completed."


async def run_crew_demo(
    customer_question: str = "What is the refund policy?",
    order_id: str = "ORD1001",
) -> dict:
    """Run the Retrieval, Lookup and Composer agents and persist execution evidence."""
    ACTUAL_TOOL_CALLS.clear()
    TOOL_RESULTS.clear()
    llm = DeterministicCrewMockLLM()

    if fixed_collection.count() == 0:
        build_collections()

    retrieval_agent = Agent(
        role="Retrieval Agent",
        goal="Retrieve relevant policy evidence using the RAG tool.",
        backstory="A support specialist that searches the local policy knowledge base.",
        tools=[rag_policy_search],
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=3,
    )
    lookup_agent = Agent(
        role="Lookup Agent",
        goal="Retrieve the requested synthetic order record.",
        backstory="A support specialist that checks order records.",
        tools=[order_status_tool],
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=3,
    )
    composer_agent = Agent(
        role="Response Composer",
        goal="Combine the actual specialist results without inventing details.",
        backstory="A response specialist that uses only the task outputs.",
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=2,
    )

    retrieval_task = Task(
        description=(
            "Retrieve policy evidence with the RAG tool.\n"
            f"Customer question: {customer_question}"
        ),
        expected_output="Retrieved policy evidence.",
        agent=retrieval_agent,
    )
    lookup_task = Task(
        description=(
            "Retrieve the requested order with the order lookup tool.\n"
            f"Order ID: {order_id}"
        ),
        expected_output="The order record returned by the lookup tool.",
        agent=lookup_agent,
    )
    composer_task = Task(
        description=(
            "Summarize the actual policy and order results from the prior tasks. "
            "Do not add facts that are absent from those results."
        ),
        expected_output="A concise response containing both specialist results.",
        agent=composer_agent,
        context=[retrieval_task, lookup_task],
    )

    crew = Crew(
        agents=[retrieval_agent, lookup_agent, composer_agent],
        tasks=[retrieval_task, lookup_task, composer_task],
        process=Process.sequential,
        verbose=False,
    )
    result = await crew.kickoff_async()

    called_tools = {entry["tool"] for entry in ACTUAL_TOOL_CALLS}
    assert {"rag_policy_search", "check_order_status"}.issubset(called_tools), (
        f"Expected both tools to run; observed {sorted(called_tools)}"
    )
    assert "rag_policy_search" in TOOL_RESULTS
    assert "check_order_status" in TOOL_RESULTS

    evidence = {
        "task": "Task 7 - CrewAI integration",
        "mode": "MOCK_LLM",
        "external_llm_api_keys_required": False,
        "agents": ["Retrieval Agent", "Lookup Agent", "Response Composer"],
        "tool_calls": ACTUAL_TOOL_CALLS,
        "tool_results": TOOL_RESULTS,
        "final_response": str(result),
        "status": "PASS",
    }
    transcript_dir = Path("transcripts")
    transcript_dir.mkdir(exist_ok=True)
    (transcript_dir / "task7_crewai.txt").write_text(
        "TASK 7 — CREWAI EXECUTION TRANSCRIPT\n"
        "Mode: deterministic MOCK_LLM; no external LLM API key.\n"
        f"Agents: {', '.join(evidence['agents'])}\n\n"
        "Actual tool invocations and results:\n"
        f"{json.dumps(ACTUAL_TOOL_CALLS, indent=2, ensure_ascii=False)}\n\n"
        f"Tool results:\n{json.dumps(TOOL_RESULTS, indent=2, ensure_ascii=False)}\n\n"
        f"Final Crew output:\n{result}\n\nPASS: both real tools were invoked.\n",
        encoding="utf-8",
    )
    Path("task7_tool_evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return evidence


def main() -> None:
    evidence = asyncio.run(run_crew_demo())
    print("CrewAI status:", evidence["status"])
    print("Agents:", ", ".join(evidence["agents"]))
    print("Tool calls:", json.dumps(evidence["tool_calls"], ensure_ascii=False))
    print("Transcript: transcripts/task7_crewai.txt")
    print("Evidence: task7_tool_evidence.json")


if __name__ == "__main__":
    main()
