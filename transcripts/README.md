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

Do not treat these instructions as proof of a passing run. The GitHub Actions
workflow commits the generated transcripts, Task 7/14 evidence, and Task 13
quality report to the submission-readiness branch only after every check passes.
For a local run, inspect the summary and commit the generated files manually.
The runner records failures and exits non-zero if any step fails.

## Evidence map

| Area | Executable evidence |
|---|---|
| Dataset generation and validation | dataset.py |
| Required knowledge-base topics and RAG index | create_knowledge_base.py, vector_store.py, 13 committed policy files |
| Retrieval and grounded-answer evaluation | evaluate_retrieval.py, evaluate_quality.py |
| Order lookup | order_lookup.py, CrewAI tool transcript |
| CrewAI orchestration and least autonomy | crew_agents.py, test_least_autonomy.py, task7_crewai.txt |
| Conversation memory | test_conversation_memory.py |
| Structured response contract | test_response_schema.py |
| PII masking and injection guardrails | test_guardrails.py |
| FastAPI and WebSocket | test_api_contract.py, test_websocket.py, test_websocket_disconnect.py |
| Structured logging | test_structured_logging.py |
| Quality evaluation (15 queries, four scores each and four averages) | evaluate_quality.py, quality_evaluation_report.json |
| AutoGen review of actual CrewAI draft | review_stage.py, task14_autogen_review.txt, task14_review_evidence.json |
| Runtime token/cost limits and risk routing | test_governance.py |
| Resilience and answer cache | test_resilience.py, test_cache.py |

The repository README is the source of truth for task descriptions and known
limitations. Task 2 and Task 3 are documented explicitly in the README and
represented in the evidence map above.
