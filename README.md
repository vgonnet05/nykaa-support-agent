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

    Both chunking strategies were evaluated using the same five in-scope
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