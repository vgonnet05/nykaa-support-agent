# Retrieval Experiments

## Experiment 1: Refund Query — Baseline

**Query:** How can I get my money back?

### Sentence-based chunking
- Top-1 source: refund_policy.txt
- Top-1 distance: 1.3653
- Top-1 context: Complete policy sentences

### Fixed-size chunking
- Top-1 source: refund_policy.txt
- Top-1 distance: 1.1760
- Top-1 context: Partial sentence; starts mid-sentence

### Observation
Both strategies retrieved the refund policy. The fixed-size collection
had a lower reported distance, but its top result provided less complete
context.

These are baseline results from the earlier knowledge-base version.

---

## Experiment 2: Similarity Threshold Calibration — Baseline

### Method
- Evaluated three in-scope and two out-of-scope queries.
- Retrieved the top-1 matching chunk from each collection.
- Calculated cosine similarity as `1 - cosine distance`.

### Baseline Results
- Highest observed out-of-scope similarity: 0.0749.
- Lowest observed in-scope similarity: 0.3174.
- Selected provisional threshold: 0.20.

### Decision Rule
- Similarity >= 0.20: accept as in-scope.
- Similarity < 0.20: reject as out-of-scope.

### Limitation
The threshold separated all five queries in the baseline test set.
A larger evaluation set is required to assess generalization.

---

## Experiment 3: Precision and Recall — Updated Knowledge Base

After updating the knowledge-base policies, both ChromaDB collections
were rebuilt and retrieval evaluation was rerun.

### Evaluation Results

| Query | Expected source | Sentence-based | Fixed-size |
|---|---|---|---|
| How can I get my money back? | refund_policy.txt | Found | Found |
| How do I track my order shipment? | order_tracking.txt | Not found | Found |
| Can I return a damaged product? | damaged_product_policy.txt | Found | Found |

Two out-of-scope queries were also tested:
- What is the capital of France?
- How can I train my pet dog?

Both strategies retrieved no expected relevant documents for these
out-of-scope queries. The similarity-threshold test also rejected both.

### Average Metrics

| Metric | Sentence-based | Fixed-size |
|---|---:|---:|
| Average precision | 0.28 | 0.67 |
| Average recall | 0.67 | 1.00 |

### Interpretation
Fixed-size chunking performed better in this evaluation, with higher
average precision and full recall across the three in-scope queries.

Sentence-based chunking missed the expected source for the order-tracking
query. Fixed-size chunking retrieved all three expected sources.

These results suggest that fixed-size chunking performed better on this
small evaluation set, but they do not establish that it will consistently
outperform sentence-based chunking.

---

## Experiment 4: Similarity Threshold — Updated Knowledge Base

### Method
The updated collections were tested using three in-scope and two
out-of-scope queries. Cosine similarity was calculated as:

`Cosine similarity = 1 - cosine distance`

### Updated Results

| Query | Type | Sentence-based | Fixed-size |
|---|---|---:|---:|
| How can I get my money back? | In-scope | 0.3593 | 0.4029 |
| How do I track my order shipment? | In-scope | 0.4675 | 0.5129 |
| Can I return a damaged product? | In-scope | 0.5708 | 0.5366 |
| What is the capital of France? | Out-of-scope | 0.0168 | 0.0747 |
| How can I train my pet dog? | Out-of-scope | 0.0346 | 0.0879 |

### Threshold Decision

**Provisional threshold: 0.20**

- Similarity >= 0.20: accept as in-scope.
- Similarity < 0.20: reject as out-of-scope.

The highest observed out-of-scope similarity was 0.0879, and the
lowest observed in-scope similarity was 0.3593. The threshold of 0.20
separates all five queries in this updated test set.

### Limitations
The evaluation uses only three in-scope and two out-of-scope queries.
The threshold is provisional and requires testing against a larger,
more diverse dataset before production use.

The retrieval metrics and similarity scores are experimental results,
not guarantees of performance on unseen queries.