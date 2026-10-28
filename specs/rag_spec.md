# RAG Specification — Nykaa Support Agent

## 1. Objective

Implement a Retrieval-Augmented Generation (RAG) pipeline that retrieves relevant information from the project's knowledge base to answer customer support questions.

The pipeline will compare two chunking strategies and evaluate their retrieval quality.

## 2. Development Environment

- Python: 3.11.15
- Sentence Transformers: 2.7.0
- ChromaDB: 1.5.9

### Embedding Model

- Model: `all-MiniLM-L6-v2`
- Embedding dimension: 384
- Status: Successfully tested

## 3. Knowledge Base

- Location: `knowledge_base/`
- Number of documents: 12
- Content: Synthetic customer support policies
- Each document contains 3–4 policy sentences.

These documents are created for the capstone and are not verified official Nykaa policies.

## 4. Chunking Strategies

### Strategy A: Fixed-Size Chunking

- Target chunk size: 200 characters
- Overlap: 40 characters

### Strategy B: Sentence-Based Chunking

- Preserve complete sentences.
- Group up to 3 sentences per chunk.

These are initial design choices and will be evaluated during retrieval testing.

## 5. Chunk Metadata

Each chunk will contain:

- `source`: Name of the originating document.
- `topic`: Policy topic.
- `chunking_strategy`: Chunking method used.

Chunk IDs must be unique and deterministic.

## 6. Vector Storage

Create two separate ChromaDB collections:

- `fixed_size_chunks`
- `sentence_chunks`

Each collection will store its corresponding chunks, embeddings, and metadata.

Use `collection.upsert()` to insert or update records.

## 7. Retrieval

Implement top-k similarity retrieval using the stored embeddings.

Retrieved chunks will provide the context for generating customer support answers.

Answers must be grounded in retrieved context rather than unsupported assumptions.

## 8. Evaluation Plan

### Similarity Threshold

- Test at least 3 in-scope queries.
- Test at least 2 out-of-scope queries.
- Measure top-1 cosine similarity.
- Select and document a threshold based on the observed results.

### Chunking Comparison

Compare both collections using the same 5 queries.

Measure document-level precision and recall, mapping retrieved chunks to their source documents and deduplicating the results.

Record per-query calculations and recommend a strategy based on the observed metrics.

## 9. Implementation Status

### Completed
- [x] Verified Python environment.
- [x] Verified Sentence Transformers and ChromaDB installations.
- [x] Loaded `all-MiniLM-L6-v2` successfully.
- [x] Confirmed the embedding dimension is 384.
- [x] Implement both chunking strategies.
- [x] Generate chunks from all 12 documents.
- [x] Generate embeddings.
- [x] Create both ChromaDB collections.
- [x] Implement top-k retrieval.

### Pending
- [] Measure similarity and establish a threshold.
- [] Compare precision and recall.