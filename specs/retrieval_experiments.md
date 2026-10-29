# Retrieval Experiments

## Experiment 1: Refund Query

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
Both strategies retrieve the refund policy. The fixed-size collection
has a lower top-1 distance, but its top result provides less complete
context. More queries are needed before recommending a strategy.

## Experiment 2: Top-1 Cosine Similarity and Threshold

### Method
- Evaluated 3 in-scope and 2 out-of-scope queries.
- Retrieved the top-1 matching chunk from each collection.
- Used cosine distance and calculated similarity as `1 - distance`.

### Results
- Highest out-of-scope similarity across both collections: 0.0749.
- Lowest in-scope similarity across both collections: 0.3174.
- Selected provisional threshold: 0.20.

### Decision Rule
- Similarity >= 0.20: accept as in-scope.
- Similarity < 0.20: reject as out-of-scope.

### Limitation
The threshold separates all five queries in this initial test set.
A larger evaluation set is required to assess generalization.

### Precision and recall evaluations Result
Sentence-based: Average precision 0.39; average recall 1.00.
Fixed-size: Average precision 0.44; average recall 1.00.
Recommendation: Fixed-size chunking performed slightly better on average precision in this small evaluation. Both achieved full recall on the three in-scope queries.
Limitation: Only three in-scope queries were used, so more testing is needed before drawing a firm conclusion.

Results
Metric	Sentence-based	Fixed-size
Average precision	0.39	0.44
Average recall	1.00	1.00


Interpretation: Fixed-size chunking has slightly higher average precision, while both strategies retrieve the expected document for all three in-scope queries.

## Task 4: Similarity Threshold Calibration

Measured top-1 cosine similarity scores using the sentence-based collection:

| Query | Type | Similarity |
|---|---|---:|
| How can I get my money back? | In-scope | 0.3174 |
| How do I track my order shipment? | In-scope | 0.5823 |
| Can I return a damaged product? | In-scope | 0.5708 |
| What is the cancellation policy? | In-scope | 0.5766 |
| How long does delivery take? | In-scope | 0.5374 |
| What is the capital of France? | Out-of-scope | 0.0168 |
| How can I train my pet dog? | Out-of-scope | 0.0127 |

**Chosen threshold: 0.20**

The highest observed out-of-scope similarity was 0.0168, while the lowest observed in-scope similarity was 0.3174. A threshold of 0.20 separates these observed examples.

This threshold is empirical and based on a small test sample. It may require recalibration with a larger evaluation dataset.