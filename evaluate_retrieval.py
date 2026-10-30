# Import the embedding model loader and both ChromaDB collections.
from vector_store import (
    load_embedding_model,
    sentence_collection,
    fixed_collection
)

# Load the local embedding model when this script needs it.
model = load_embedding_model()
# Expected relevant policy documents for each evaluation query.

evaluation_cases = [
    {
        "query": "What is the refund timeline for a cash-on-delivery order?",
        "expected_sources": ["refund_policy.txt"]
    },
    {
        "query": "Which countries can Nykaa ship orders to internationally?",
        "expected_sources": ["international_shipping_policy.txt"]
    },
    {
        "query": "Can I return a damaged product?",
        "expected_sources": ["damaged_product_policy.txt"]
    },
    {
        "query": "How long does delivery take after dispatch?",
        "expected_sources": ["delivery_policy.txt"]
    },
    {
        "query": "Can I exchange the size of my footwear?",
        "expected_sources": ["exchange_policy.txt"]
    },
    {
        "query": "What is the capital of France?",
        "expected_sources": []
    },
    {
        "query": "How can I train my pet dog?",
        "expected_sources": []
    }
]

# Retrieve the top-k chunks and return their unique source documents.
def retrieve_documents(query, collection, k=3):

    # Convert the customer query into an embedding.
    query_embedding = model.encode(query).tolist()

    # Retrieve the k most similar chunks from ChromaDB.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    # Extract the source document for each retrieved chunk.
    sources = [
        metadata["source"]
        for metadata in results["metadatas"][0]
    ]

    # Remove duplicate source documents while preserving their order.
    unique_sources = list(dict.fromkeys(sources))

    # Return the unique source documents for evaluation.
    return unique_sources


# Calculate document-level precision and recall for one query.
def calculate_metrics(retrieved_sources, expected_sources):

    # Convert lists to sets so we can compare unique document names.
    retrieved = set(retrieved_sources)
    expected = set(expected_sources)

    # Find documents that are both retrieved and relevant.
    relevant_retrieved = retrieved.intersection(expected)

    # Count the relevant documents that were retrieved.
    true_positives = len(relevant_retrieved)

    # Count retrieved documents that were not expected to be relevant.
    false_positives = len(retrieved - expected)

    # Count relevant documents that were not retrieved.
    false_negatives = len(expected - retrieved)

    # Calculate precision, avoiding division by zero.
    precision = (
        true_positives / len(retrieved)
        if retrieved
        else 0.0
    )

    # Recall is undefined when no relevant documents are expected.
    recall = (
        true_positives / len(expected)
        if expected
        else None
    )

    # Return the metrics and counts for reporting.
    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall
    }
# Store metrics for the in-scope queries.
sentence_all_metrics = []
fixed_all_metrics = []

# Test each evaluation query against both chunking strategies.      
for case in evaluation_cases:

    # Get the customer's question.
    query = case["query"]

    # Get the expected relevant documents.
    expected_sources = case["expected_sources"]

    print("\n" + "=" * 60)
    print(f"Query: {query}")
    print(f"Expected sources: {expected_sources}")

    # Search the sentence-based collection.
    sentence_sources = retrieve_documents(
        query,
        sentence_collection
    )

    # Search the fixed-size collection.
    fixed_sources = retrieve_documents(
        query,
        fixed_collection
    )

    # Calculate precision and recall for each strategy.
    sentence_metrics = calculate_metrics(
        sentence_sources, expected_sources
    )
    fixed_metrics = calculate_metrics(
        fixed_sources, expected_sources
    )

    # Store metrics only for in-scope queries.
    if expected_sources:
        sentence_all_metrics.append(sentence_metrics)
        fixed_all_metrics.append(fixed_metrics)

    # Display the evaluation metrics for every query.
    print(
        f"Sentence-based: Precision={sentence_metrics['precision']:.2f}, "
        f"Recall={sentence_metrics['recall']}"
    )
    print(
        f"Fixed-size: Precision={fixed_metrics['precision']:.2f}, "
        f"Recall={fixed_metrics['recall']}"
    )

    # Display the retrieved source documents.
    print(f"Sentence-based results: {sentence_sources}")
    print(f"Fixed-size results: {fixed_sources}")


# Calculate average metrics for in-scope queries.
print("\n--- Average metrics (in-scope queries only) ---")

for name, metrics_list in [
    ("Sentence-based", sentence_all_metrics),
    ("Fixed-size", fixed_all_metrics)
]:
    avg_precision = sum(
        item["precision"] for item in metrics_list
    ) / len(metrics_list)

    avg_recall = sum(
        item["recall"] for item in metrics_list
    ) / len(metrics_list)

    print(
        f"{name}: Average precision={avg_precision:.2f}, "
        f"Average recall={avg_recall:.2f}"
    )