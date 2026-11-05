# nykaa-support-agent

A hands-on learning project to understand and build an Agentic AI support agent using RAG, CrewAI, AutoGen, memory, guardrails, and FastAPI through step-by-step implementation.

**Completed track:** Nykaa (E-commerce & Retail)

## Task 1: Dataset Design

- **Random seed:** 50
- **Categories:** Apparel, Electronics, Home, Footwear, Beauty — 10 records each.
- **Statuses:** Placed (5), Shipped (10), Delivered (20), Returned (7), Refunded (8).
- **Order values:** Random integers between ₹100 and ₹10,000.
- **Order age:** Random integers between 0 and 30 days.
- **Delayed shipments:** 10 of 50 records (20%), within the required 10–30% range.

These choices provide balanced category coverage, realistic variation in
order states and values, and sufficient delayed shipments to test escalation.

## Task 2: Knowledge Base

The repository contains 13 policy documents: the 12 required policy topics plus
a supplemental shipping/tracking document. The required topics are return windows
by category, COD refund timelines, delivery SLAs, reverse-pickup eligibility,
warranty terms by category, cancellation, loyalty-point redemption, payment
failure/retry, size exchange, damaged-item claims, international shipping
restrictions, and the customer-support escalation matrix. Reverse-pickup
eligibility is documented separately in reverse_pickup_policy.txt.

The numerical timelines and conditions are fictional capstone assumptions,
not verified official Nykaa policies. The three manually maintained files
(return_policy.txt, shipping_policy.txt, and reverse_pickup_policy.txt) are
preserved when create_knowledge_base.py is rerun.

## Task 3: Chunking and Vector Storage

chunking.py implements fixed-size chunks with overlap and sentence-based
chunking. vector_store.py embeds both chunk sets with the local
all-MiniLM-L6-v2 Sentence Transformers model and indexes them into separate
ChromaDB collections: fixed_size_chunks and sentence_chunks. Run
python vector_store.py after creating the policy documents to rebuild both
collections.

## Task 4: Grounded Answer Generation

The system retrieves the top three policy chunks and returns their
content as the answer under MOCK_LLM. It does not call an external
language model.

The similarity threshold is set to 0.20 based on measured retrieval
results. Similarity is calculated as 1 minus cosine distance. If the
top result falls below this threshold, the system returns:
"I don't know based on the available policy information."

Testing covered five in-scope queries and two out-of-scope queries.
All five in-scope queries were accepted, and both out-of-scope queries
triggered the fallback response.

| Query | Top similarity | Expected scope | Result |
|---|---:|---|---|
| How can I get my money back? | 0.3613 | In scope | Accepted |
| Which countries can Nykaa ship orders to internationally? | 0.7025 | In scope | Accepted |
| Can I return a damaged product? | 0.5879 | In scope | Accepted |
| What is the cancellation policy? | 0.5805 | In scope | Accepted |
| How long does delivery take? | 0.5374 | In scope | Accepted |
| What is the capital of France? | 0.0168 | Out of scope | Fallback |
| How can I train my pet dog? | 0.0462 | Out of scope | Fallback |

The threshold is provisional because it was calibrated using a small
sample. The delivery query also retrieved a partially unrelated
sentence, demonstrating that similarity alone does not guarantee
relevance.

## Task 5: Retrieval Evaluation

Both chunking strategies were evaluated using five in-scope
queries and two out-of-scope queries. Evaluation uses document-level
precision and recall, with the expected source document specified for
each in-scope query.

| Metric | Sentence-based chunking | Fixed-size chunking |
|---|---:|---:|
| Average precision | 0.37 | 0.47 |
| Average recall | 1.00 | 1.00 |

Fixed-size chunking achieved higher average precision (0.47 versus
0.37), while both strategies achieved an average recall of 1.00.
This means both retrieved the expected document for every in-scope
query, but fixed-size chunking returned fewer irrelevant documents
on average.

Out-of-scope queries returned irrelevant policy documents, resulting
in zero precision. Recall is not applicable to these queries because
they have no expected source documents. The similarity threshold in
Task 4 provides a separate mechanism for rejecting unsupported
questions.

### Per-Query Precision and Recall

For each in-scope query:

- **Precision** = relevant retrieved documents / total retrieved documents.
- **Recall** = relevant retrieved documents / total expected relevant documents.

The expected source document for each query was one policy file.

| Query | Sentence Precision | Fixed-Size Precision | Recall (Both) |
|---|---:|---:|---:|
| COD refund timeline | 1/3 = 0.33 | 1/2 = 0.50 | 1.00 |
| International shipping | 1/3 = 0.33 | 1/2 = 0.50 | 1.00 |
| Damaged product return | 1/3 = 0.33 | 1/3 = 0.33 | 1.00 |
| Delivery time | 1/2 = 0.50 | 1/2 = 0.50 | 1.00 |
| Footwear size exchange | 1/3 = 0.33 | 1/2 = 0.50 | 1.00 |

### Chunking Strategy Recommendation

Fixed-size chunking is the preferred strategy for this experiment. It achieved average precision of **0.47**, compared with **0.37** for sentence-based chunking, while both achieved average recall of **1.00**. Therefore, fixed-size chunking retrieved the expected policy documents while returning fewer irrelevant documents on average. This conclusion is limited to the five in-scope evaluation queries.

## Task 6: Order Lookup and Escalation Score

The `check_order_status(record_id: str) -> dict` function looks up an order by its unique record ID and returns its status, order value in INR, and escalation score. If the order does not exist, it returns an error.

### Escalation Formula

The score combines delayed-shipment status and order age:

- **Delayed-shipment factor:** 1.0 if delayed; otherwise 0.0.
- **Normalized order age:** `days_since_created / 30`.
- **Escalation score:** `(0.6 × delayed-shipment factor) + (0.4 × normalized order age)`.

The score ranges from 0.0 to 1.0. Delayed shipments receive a higher weight because delivery delays require attention, while older orders also increase the score.

### Escalation Threshold

An escalation threshold of **0.60** is proposed. Orders scoring 0.60 or higher should be flagged for review. This is a project-defined threshold, not an official Nykaa rule.

The dataset contains 50 orders, including 10 delayed shipments (20%), within the required 10–30% range. The threshold should be evaluated against the generated dataset before being treated as an effective escalation rule.

### Validation

- Existing order `ORD1001`: lookup successful; escalation score 0.36.
- Non-existing order `ORD9999`: returns `{"error": "Order not found"}`.

### Threshold Validation Results

Testing the 0.60 threshold against the 50 generated orders flagged
10 orders (20% of the dataset). All 10 delayed shipments were flagged,
and no non-delayed orders were flagged.

This result supports the threshold for the current synthetic dataset.
However, the dataset is small and the delayed-shipment flag contributes
60% to the score, so further testing would be needed before applying
this threshold to real customer orders.

## Task 7: CrewAI Integration

The CrewAI workflow defines three agent roles:
- **Retrieval agent:** retrieves relevant policy information.
- **Lookup agent:** handles order lookups.
- **Composer agent:** prepares the response.

The reproducible implementation is in crew_agents.py. It defines the Retrieval, Lookup and Response Composer agents and invokes the actual local RAG and order-lookup tools through CrewAI kickoff_async(). The Composer task uses output_pydantic=SupportResponse, and the resulting CrewOutput.pydantic value is validated in code.

Only the Lookup Agent receives check_order_status. Retrieval receives only rag_policy_search, and the Composer receives no tools. Runtime assertions and test_least_autonomy.py verify this least-autonomy restriction. The run writes task7_tool_evidence.json plus transcripts/task7_crewai.txt.

Run python crew_agents.py after building the knowledge base and vector collections. The deterministic CrewAI BaseLLM implementation makes no external LLM calls. Set MOCK_LLM=true, CREWAI_DISABLE_TELEMETRY=true and OTEL_SDK_DISABLED=true.

## Task 8: Conversation Memory

`conversation_memory.py` demonstrates session-scoped in-memory conversation history.

Tests check that messages remain available within the same session and that separate sessions have isolated histories.

**Limitation:** Memory is lost when the process restarts. The WebSocket endpoint stores conversation history, but the current RAG answer-generation workflow does not use that history to contextualize answers.

## Task 9: Structured Response Schema

`response_schema.py` defines a Pydantic `SupportResponse` model with:
- `answer`
- `source_documents`
- `requires_escalation`

The CrewAI Composer task declares this model through output_pydantic=SupportResponse. crew_agents.py validates the returned structured CrewOutput against this Pydantic model and records the validated fields in its evidence transcript. test_response_schema.py also checks the schema independently. The FastAPI layer has its own request/response models.

## Task 10: Guardrails

`guardrails.py` implements basic safeguards:
- Masks supported Indian mobile-number patterns.
- Detects a limited set of prompt-injection phrases.
- Blocks detected injection attempts in the support workflow.

**Limitations:** The masking does not cover every form of personal information, and the pattern-based injection detector is not comprehensive.

## Task 11: FastAPI

`api.py` provides these interfaces:

| Endpoint | Purpose |
|---|---|
| `POST /ask` | Process a support question, optionally with an order ID |
| `POST /add-document` | Add a `.txt` policy document |
| `WS /ws/chat` | Exchange support messages over WebSocket |

The document endpoint validates filenames and content, rejects duplicate filenames, and indexes accepted documents in both vector collections.

## Task 12: Structured Logging

`structured_logging.py` appends JSON Lines records to `logs/requests.jsonl`.

Each record contains a UTC timestamp, trace ID, endpoint, masked request text, duration in milliseconds, and request status. The HTTP endpoints and WebSocket message handler log in finally blocks, including rejected/error paths.

test_structured_logging.py verifies JSONL fields, unique trace IDs, timing, PII masking, and one log entry for representative /ask, /add-document, and /ws/chat requests. Logs are generated at runtime and excluded from version control. Phone-number and card-suffix masking cover the fixed-format PII required by the brief; this is not a general-purpose PII detector.

## Task 13: Quality Evaluation

`evaluate_quality.py` evaluates 15 support queries using the sentence-based ChromaDB collection and writes `quality_evaluation_report.json`.

The evaluator runs in deterministic `MOCK_LLM` mode and passes the rubric's JUDGE_PROMPT, expected answer, candidate response, and retrieved sources to a local mock judge. The mock judge uses transparent deterministic checks rather than a real external LLM call. All 15 queries receive numeric Accuracy, Grounding, Completeness, and Safety scores, including the prompt-injection refusal case, and the report contains all four averages. The 12 in-scope cases cover the 12 required knowledge-base topics; the remaining three are two out-of-scope questions and one prompt-injection case.

Run the evaluation after building the knowledge base:

```bash
python create_knowledge_base.py
python evaluate_quality.py
```

Treat these scores as regression checks for the current synthetic dataset, not independent validation of real-world answer quality. The answer generator currently returns retrieved policy text rather than composing a new response with an external language model.

## Task 14: AutoGen Review

The reproducible implementation is in review_stage.py. It first runs the actual CrewAI crew and passes its Composer draft plus retrieved RAG/order context into a two-agent AutoGen RoundRobinGroupChat. The FinalEditor returns a structured Pydantic Verdict. One scenario approves the actual draft unchanged; the second injects an unsupported 30-day return promise and verifies that the review stage removes it. Run python review_stage.py. The run writes transcripts/task14_autogen_review.txt and task14_review_evidence.json.

This demonstrates AutoGen orchestration and structured verdict handling for the defined deterministic scenarios. It does not prove that a real LLM reviewer will reliably detect all hallucinations or unsafe responses.

## Task 15: Runtime Limits and Risk Classification

`runtime_limits.py` defines:
- Maximum estimated input: 2,000 tokens
- Maximum estimated output: 500 tokens
- Illustrative request cost cap: 0.20
- Illustrative input price: 100 per million tokens
- Illustrative output price: 250 per million tokens

Token estimation uses approximately one token per four characters. These are estimates, not actual tokenizer counts or live provider prices.

The risk classifier assigns low, medium, or high risk using a limited keyword list. The overall system is classified as **Medium risk** because the rubric explicitly places customer-support tickets in the Medium category. The agent handles support questions and synthetic order information; it does not make medical, hiring, or other high-impact decisions. Requests matching high-risk fraud or unauthorized-payment indicators are routed to a human-support escalation response.

**Least autonomy:** Only the Lookup Agent is wired with check_order_status; Retrieval and Composer do not receive that tool. The crew checks this permission boundary at runtime and test_least_autonomy.py verifies the actual attached tool lists.

**Runtime budget:** The workflow enforces estimated input/output token limits and a per-request cost cap. test_governance.py demonstrates both an oversized token request and a separate request whose estimated cost exceeds the configured cap. These prices are illustrative estimates, not actual provider billing or cumulative budget enforcement.

## Task 16: In-Memory Answer Cache

`grounded_generation.py` caches answers using the normalized query and vector collection name. It tracks cache hits and misses and provides a function to clear the cache and reset its counters.

**Limitation:** The cache is lost on process restart. Cached answers may also become stale after policy documents change unless the cache is cleared.

**Verification:** Run `python test_cache.py` to verify:
- Repeated queries with different capitalization and whitespace produce a cache hit.
- The repeated query avoids a redundant retrieval call (1 retrieval call across 2 requests).
- Different vector collections use separate cache entries (2 retrieval calls across 2 collections).

Both cache tests passed. The cache uses an in-memory dictionary and is not persistent across process restarts.

## Setup and Installation

The project is designed to run in deterministic MOCK_LLM mode without any external LLM-provider API keys. The support workflow uses local Sentence Transformers embeddings and ChromaDB; CrewAI and AutoGen use local deterministic mock clients.

Set the following environment variables before running the demonstrations:

~~~bash
export MOCK_LLM=true
export CREWAI_DISABLE_TELEMETRY=true
export OTEL_SDK_DISABLED=true
~~~

The first setup may download the all-MiniLM-L6-v2 embedding model from Hugging Face. This is a local embedding model, not an LLM API call, and may require internet access on first use.

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows, activate with `.venv/Scripts/activate`.

## Build the Knowledge Base

Run from the project root:

```bash
python create_knowledge_base.py
python vector_store.py
```

The first command creates the policy text files. The second command builds both local ChromaDB collections and generates their embeddings in `chroma_db/`.

## Run the API

```bash
uvicorn api:app --reload
```

Open `/docs` on the local server for interactive API documentation.

## Run Evaluations

```bash
python evaluate_retrieval.py
python evaluate_quality.py
```

## Run Test Scripts

Run the complete submission check from the repository root:

~~~bash
python run_submission_checks.py
~~~

The runner sets MOCK_LLM=true, disables CrewAI telemetry, removes common LLM-provider API-key variables from child processes, executes the demonstration and regression scripts, and saves command output under transcripts/. It exits non-zero if any command fails.

The individual checks can also be run separately:

~~~bash
python test_guardrails.py
python test_conversation_memory.py
python test_response_schema.py
python test_governance.py
python test_least_autonomy.py
python test_resilience.py
python test_cache.py
python test_api_contract.py
python test_structured_logging.py
python test_websocket.py
python test_websocket_disconnect.py
python crew_agents.py
python review_stage.py
~~~

After a successful run, inspect and commit the generated files under transcripts/. A pytest run that discovers zero tests does not demonstrate a passing test suite.

## Known Limitations

1. Policy documents contain fictional capstone assumptions, not verified official Nykaa policies.
2. The workflow returns retrieved policy text rather than generating answers with a real LLM.
3. Retrieval can include irrelevant chunks; the similarity threshold is provisional.
4. Quality scores come from a deterministic mock evaluator and are not independent validation.
5. PII masking and prompt-injection detection cover limited patterns.
6. Conversation history and the answer cache are in memory and are lost on restart.
7. High-risk requests are routed to a human-review escalation response; classification is based on a limited keyword list.
8. Token and cost estimates are illustrative, not actual model billing.
9. Production readiness has not been established through independent evaluation, security review, or real-world testing.

Submission transcripts and evidence are generated under transcripts/ by run_submission_checks.py. See transcripts/README.md for the evidence map.

## Summary

This capstone combines synthetic order data, a policy knowledge base, embedding-based retrieval, chunking experiments, order lookup, CrewAI and AutoGen exercises, memory, guardrails, FastAPI, structured logging, runtime limits, evaluation, and caching.

It demonstrates these components in a deterministic learning environment. Evaluation results and limitations should be considered before extending the system to real customer-support use cases.
