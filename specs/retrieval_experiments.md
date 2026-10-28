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