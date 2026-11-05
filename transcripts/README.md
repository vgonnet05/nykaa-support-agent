# Submission transcripts

Run the complete deterministic demonstration suite from the repository root:

~~~bash
python -m pip install -r requirements.txt
export MOCK_LLM=true
export CREWAI_DISABLE_TELEMETRY=true
export OTEL_SDK_DISABLED=true
python run_submission_checks.py
~~~

The runner creates one text transcript per command under this directory and a
submission_check_summary.md file. CrewAI and AutoGen also create their
scenario-specific transcripts:

- task7_crewai.txt — actual RAG and order-lookup tool invocations, tool results,
  and the final Crew output.
- task14_autogen_review.txt — clean-draft approval and planted-hallucination
  revision, including structured verdicts.

The runner deliberately removes common external LLM API-key variables from the
child-process environment. The project uses deterministic mock LLM clients for
CrewAI and AutoGen; RAG uses local Sentence Transformers embeddings and ChromaDB.
The embedding model may need to be downloaded from Hugging Face on first run,
so internet access may be needed for initial setup. No LLM-provider API key is
required.

Do not treat these instructions as proof of a passing run. Commit the generated
transcripts and summary only after run_submission_checks.py exits successfully.
The runner records failures and exits non-zero if any step fails.

## Evidence map

| Area | Executable evidence |
|---|---|
| Dataset generation and validation | dataset.py |
| Knowledge-base creation and RAG index | create_knowledge_base.py, vector_store.py |
| Retrieval and grounded-answer evaluation | evaluate_retrieval.py, evaluate_quality.py |
| Order lookup | order_lookup.py, CrewAI tool transcript |
| CrewAI orchestration | crew_agents.py, task7_crewai.txt |
| Conversation memory | test_conversation_memory.py |
| Structured response contract | test_response_schema.py |
| PII masking and injection guardrails | test_guardrails.py |
| FastAPI and WebSocket | test_api_contract.py, test_websocket.py, test_websocket_disconnect.py |
| Structured logging | test_structured_logging.py |
| Quality evaluation | evaluate_quality.py |
| AutoGen review | review_stage.py, task14_autogen_review.txt |
| Runtime limits and risk routing | test_governance.py |
| Resilience and answer cache | test_resilience.py, test_cache.py |

The repository README is the source of truth for task descriptions and known
limitations. If the course rubric defines additional Tasks 2 or 3 not listed
there, add their exact acceptance criteria and demonstrations before submission.
