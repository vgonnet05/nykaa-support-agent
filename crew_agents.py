"""Three-agent CrewAI demonstration using deterministic local tools and a mock LLM."""
from __future__ import annotations

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
from response_schema import SupportResponse
from vector_store import build_collections, fixed_collection, search_policy

require_mock_llm()

ACTUAL_TOOL_CALLS: list[dict] = []
TOOL_RESULTS: dict[str, object] = {}


@tool("rag_policy_search")
def rag_policy_search(query: str) -> str:
    """Retrieve policy evidence from the local ChromaDB knowledge base."""
    result = generate_grounded_answer(query, fixed_collection)
    retrieved = search_policy(query, fixed_collection, k=3)
    sources = list(dict.fromkeys(
        item["source"]
        for item in retrieved["metadatas"][0]
        if item and "source" in item
    ))
    TOOL_RESULTS["rag_policy_search"] = result
    TOOL_RESULTS["rag_sources"] = sources
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
            sources = TOOL_RESULTS.get("rag_sources", [])
            if not rag or not order:
                return "Final Answer: ERROR — required specialist tool results are missing."
            structured = {
                "answer": (
                    "Policy evidence:\n"
                    f"{rag}\n\n"
                    "Order lookup:\n"
                    f"{json.dumps(order, ensure_ascii=False)}"
                ),
                "source_documents": sources,
                "requires_escalation": False,
            }
            return json.dumps(structured, ensure_ascii=False)

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


def get_tool_permissions(agents: dict[str, Agent]) -> dict[str, list[str]]:
    """Return each agent's actual attached tools for least-autonomy verification."""
    return {
        role: sorted(getattr(tool_item, "name", str(tool_item)) for tool_item in agent.tools)
        for role, agent in agents.items()
    }


def build_crew(
    llm: DeterministicCrewMockLLM,
    customer_question: str = "What is the refund policy?",
    order_id: str = "ORD1001",
):
    """Build the three agents and tasks; only Lookup Agent receives the order tool."""
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
            "Return JSON with answer, source_documents, and requires_escalation. "
            "Do not add facts absent from the task results."
        ),
        expected_output=(
            "A valid SupportResponse JSON object with answer (string), "
            "source_documents (array of filenames), and requires_escalation (boolean)."
        ),
        agent=composer_agent,
        context=[retrieval_task, lookup_task],
        output_pydantic=SupportResponse,
    )

    crew = Crew(
        agents=[retrieval_agent, lookup_agent, composer_agent],
        tasks=[retrieval_task, lookup_task, composer_task],
        process=Process.sequential,
        verbose=False,
    )
    agents = {
        "Retrieval Agent": retrieval_agent,
        "Lookup Agent": lookup_agent,
        "Response Composer": composer_agent,
    }
    return crew, agents


def run_crew_demo(
    customer_question: str = "What is the refund policy?",
    order_id: str = "ORD1001",
) -> dict:
    """Run the crew, validate its structured response and persist execution evidence."""
    ACTUAL_TOOL_CALLS.clear()
    TOOL_RESULTS.clear()
    llm = DeterministicCrewMockLLM()

    if fixed_collection.count() == 0:
        build_collections()

    crew, agents = build_crew(llm, customer_question, order_id)
    permissions = get_tool_permissions(agents)

    # Least autonomy: only Lookup Agent may invoke check_order_status.
    assert "check_order_status" in permissions["Lookup Agent"]
    assert "check_order_status" not in permissions["Retrieval Agent"]
    assert "check_order_status" not in permissions["Response Composer"]
    assert "rag_policy_search" in permissions["Retrieval Agent"]
    assert "rag_policy_search" not in permissions["Lookup Agent"]

    result = crew.kickoff()

    structured_response = getattr(result, "pydantic", None)
    if structured_response is None:
        raw_output = getattr(result, "raw", str(result))
        structured_response = SupportResponse.model_validate_json(raw_output)
    elif not isinstance(structured_response, SupportResponse):
        structured_response = SupportResponse.model_validate(structured_response)

    called_tools = {entry["tool"] for entry in ACTUAL_TOOL_CALLS}
    assert {"rag_policy_search", "check_order_status"}.issubset(called_tools), (
        f"Expected both tools to run; observed {sorted(called_tools)}"
    )
    assert "rag_policy_search" in TOOL_RESULTS
    assert "check_order_status" in TOOL_RESULTS
    assert structured_response.answer
    assert structured_response.source_documents

    evidence = {
        "task": "Task 7 - CrewAI integration",
        "mode": "MOCK_LLM",
        "external_llm_api_keys_required": False,
        "agents": list(agents),
        "tool_permissions": permissions,
        "least_autonomy_assertion": "PASS",
        "tool_calls": ACTUAL_TOOL_CALLS,
        "tool_results": TOOL_RESULTS,
        "structured_response": structured_response.model_dump(),
        "final_response": structured_response.model_dump_json(indent=2),
        "status": "PASS",
    }
    transcript_dir = Path("transcripts")
    transcript_dir.mkdir(exist_ok=True)
    (transcript_dir / "task7_crewai.txt").write_text(
        "TASK 7 — CREWAI EXECUTION TRANSCRIPT\n"
        "Mode: deterministic MOCK_LLM; no external LLM API key.\n"
        f"Agents: {', '.join(evidence['agents'])}\n\n"
        "Actual tool permissions:\n"
        f"{json.dumps(permissions, indent=2)}\n\n"
        "Least-autonomy assertions: PASS\n"
        "Only Lookup Agent has check_order_status; Retrieval and Composer do not.\n\n"
        "Actual tool invocations:\n"
        f"{json.dumps(ACTUAL_TOOL_CALLS, indent=2, ensure_ascii=False)}\n\n"
        f"Tool results:\n{json.dumps(TOOL_RESULTS, indent=2, ensure_ascii=False)}\n\n"
        "Validated Pydantic SupportResponse:\n"
        f"{structured_response.model_dump_json(indent=2)}\n\n"
        "PASS: both tools ran and the final response passed Pydantic validation.\n",
        encoding="utf-8",
    )
    Path("task7_tool_evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return evidence


def main() -> None:
    evidence = run_crew_demo()
    print("CrewAI status:", evidence["status"])
    print("Agents:", ", ".join(evidence["agents"]))
    print("Tool permissions:", json.dumps(evidence["tool_permissions"]))
    print("Tool calls:", json.dumps(evidence["tool_calls"], ensure_ascii=False))
    print("Structured response validated:", bool(evidence["structured_response"]))
    print("Transcript: transcripts/task7_crewai.txt")
    print("Evidence: task7_tool_evidence.json")


if __name__ == "__main__":
    main()
