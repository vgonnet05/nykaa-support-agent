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

The workflow uses CrewAI's kickoff mechanism. Supporting notebook and evidence files are included in the repository.

The deterministic mock setup demonstrates orchestration, not production LLM response quality.

## Task 8: Conversation Memory

`conversation_memory.py` demonstrates session-scoped in-memory conversation history.

Tests check that messages remain available within the same session and that separate sessions have isolated histories.

**Limitation:** Memory is lost when the process restarts. The WebSocket endpoint stores conversation history, but the current RAG answer-generation workflow does not use that history to contextualize answers.

## Task 9: Structured Response Schema

`response_schema.py` defines a Pydantic `SupportResponse` model with:
- `answer`
- `source_documents`
- `requires_escalation`

This defines a structured response contract. The current API uses its own response model, so this schema should not be assumed to validate every API response.

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

Each record contains a UTC timestamp, trace ID, endpoint, masked request text, duration in milliseconds, and request status.

Logs are generated at runtime and excluded from version control. Phone-number masking does not guarantee that all sensitive information is removed.

## Task 13: Quality Evaluation

`evaluate_quality.py` evaluates 15 support queries using the sentence-based ChromaDB collection and writes `quality_evaluation_report.json`.

The evaluator is deterministic and runs in `MOCK_LLM` mode. It checks expected policy facts and retrieved source metadata; it does **not** call a real LLM judge. Prompt-injection cases are scored only for safety because accuracy, grounding, and completeness are not applicable to a blocked request. The report records the sample count for each metric so non-applicable scores do not distort averages.

Run the evaluation after building the knowledge base:

```bash
python create_knowledge_base.py
python evaluate_quality.py
```

Treat these scores as regression checks for the current synthetic dataset, not independent validation of real-world answer quality. The answer generator currently returns retrieved policy text rather than composing a new response with an external language model.

## Task 14: AutoGen Review

The notebook includes an AutoGen review exercise using structured Pydantic verdicts and deterministic mock scenarios.

This demonstrates orchestration and structured review for the tested scenarios. It does not prove that a real LLM reviewer will reliably detect all hallucinations or unsafe responses.

## Task 15: Runtime Limits and Risk Classification

`runtime_limits.py` defines:
- Maximum estimated input: 2,000 tokens
- Maximum estimated output: 500 tokens
- Illustrative request cost cap: 0.20
- Illustrative input price: 100 per million tokens
- Illustrative output price: 250 per million tokens

Token estimation uses approximately one token per four characters. These are estimates, not actual tokenizer counts or live provider prices.

The risk classifier assigns low, medium, or high risk using a limited keyword list.

**Governance:** High-risk requests are escalated for human review by `handle_support_request` in `support_workflow.py`. This is a keyword-based project rule, not a comprehensive risk assessment. The cost calculation is illustrative and does not demonstrate actual model billing or cumulative budget enforcement.

## Task 16: In-Memory Answer Cache

`grounded_generation.py` caches answers using the normalized query and vector collection name. It tracks cache hits and misses and provides a function to clear the cache and reset its counters.

**Limitation:** The cache is lost on process restart. Cached answers may also become stale after policy documents change unless the cache is cleared.

**Verification:** Run `python test_cache.py` to verify:
- Repeated queries with different capitalization and whitespace produce a cache hit.
- The repeated query avoids a redundant retrieval call (1 retrieval call across 2 requests).
- Different vector collections use separate cache entries (2 retrieval calls across 2 collections).

Both cache tests passed. The cache uses an in-memory dictionary and is not persistent across process restarts.

## Setup and Installation

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
```

This creates the local ChromaDB collections in `chroma_db/`.

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

```bash
python test_guardrails.py
python test_conversation_memory.py
python test_websocket.py
python test_websocket_disconnect.py
```

Verify each script's result before reporting it as passing. A pytest run that discovers zero tests does not demonstrate a passing test suite.

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

## Summary

This capstone combines synthetic order data, a policy knowledge base, embedding-based retrieval, chunking experiments, order lookup, CrewAI and AutoGen exercises, memory, guardrails, FastAPI, structured logging, runtime limits, evaluation, and caching.

It demonstrates these components in a deterministic learning environment. Evaluation results and limitations should be considered before extending the system to real customer-support use cases.
