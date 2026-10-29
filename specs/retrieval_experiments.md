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