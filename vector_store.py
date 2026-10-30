# Import the library used to create text embeddings.
from sentence_transformers import SentenceTransformer

# Import ChromaDB for storing and searching policy embeddings.
import chromadb

# Import functions that load documents and split them into chunks.
from chunking import (
    load_documents,
    sentence_based_chunking,
    fixed_size_chunking
)


# --------------------------------------------------
# 1. LOAD THE EMBEDDING MODEL WHEN NEEDED
# --------------------------------------------------

# None means the model has not been loaded yet.
# This avoids loading the model just because another file imports this module.
model = None


def load_embedding_model():
    """Load the local embedding model once and reuse it."""
    global model

    # Load the model only if it has not already been loaded.
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

        # Display the number of dimensions in each embedding.
        print(
            "Embedding dimension:",
            model.get_sentence_embedding_dimension()
        )

    return model


# --------------------------------------------------
# 2. CONNECT TO THE VECTOR DATABASE
# --------------------------------------------------

# Store the database locally in the chroma_db directory.
client = chromadb.PersistentClient(path="./chroma_db")


# Get the sentence-based collection, creating it if necessary.
# Cosine distance measures the difference between embeddings.
sentence_collection = client.get_or_create_collection(
    name="sentence_chunks",
    metadata={"hnsw:space": "cosine"}
)


# Get the fixed-size collection, creating it if necessary.
# Both collections use cosine distance for a fair comparison.
fixed_collection = client.get_or_create_collection(
    name="fixed_size_chunks",
    metadata={"hnsw:space": "cosine"}
)


# --------------------------------------------------
# 3. BUILD AND POPULATE THE COLLECTIONS
# --------------------------------------------------

def build_collections():
    """Load documents, create chunks, generate embeddings and store them."""

    # Load the embedding model before generating embeddings.
    embedding_model = load_embedding_model()

    # Load all policy documents from the knowledge_base directory.
    documents = load_documents()

    # Split the documents using sentence-based chunking.
    sentence_chunks = sentence_based_chunking(documents)

    # Split the same documents using fixed-size chunks with overlap.
    fixed_chunks = fixed_size_chunking(documents)

    # Convert each sentence-based chunk into a numerical embedding.
    sentence_embeddings = embedding_model.encode(
        [chunk["text"] for chunk in sentence_chunks]
    )

    # Convert each fixed-size chunk into a numerical embedding.
    fixed_embeddings = embedding_model.encode(
        [chunk["text"] for chunk in fixed_chunks]
    )
    # Clear existing records so renamed or deleted documents cannot remain.
    sentence_ids = sentence_collection.get()["ids"]
    if sentence_ids:
        sentence_collection.delete(ids=sentence_ids)

    fixed_ids = fixed_collection.get()["ids"]
    if fixed_ids:
        fixed_collection.delete(ids=fixed_ids)
    # Insert or update the sentence-based chunks in ChromaDB.
    sentence_collection.upsert(
        ids=[chunk["id"] for chunk in sentence_chunks],
        embeddings=sentence_embeddings.tolist(),
        documents=[chunk["text"] for chunk in sentence_chunks],
        metadatas=[
            {
                "source": chunk["source"],
                "topic": chunk["topic"],
                "chunking_strategy": chunk["chunking_strategy"]
            }
            for chunk in sentence_chunks
        ]
    )

    # Insert or update the fixed-size chunks in ChromaDB.
    fixed_collection.upsert(
        ids=[chunk["id"] for chunk in fixed_chunks],
        embeddings=fixed_embeddings.tolist(),
        documents=[chunk["text"] for chunk in fixed_chunks],
        metadatas=[
            {
                "source": chunk["source"],
                "topic": chunk["topic"],
                "chunking_strategy": chunk["chunking_strategy"]
            }
            for chunk in fixed_chunks
        ]
    )

    # Display the number of chunks and embeddings created.
    print("\n--- Collection build summary ---")
    print("Sentence-based chunks:", len(sentence_chunks))
    print("Fixed-size chunks:", len(fixed_chunks))
    print("Sentence-based embeddings:", sentence_embeddings.shape)
    print("Fixed-size embeddings:", fixed_embeddings.shape)

    # Display the total records stored in each collection.
    print("Sentence collection records:", sentence_collection.count())
    print("Fixed-size collection records:", fixed_collection.count())


# --------------------------------------------------
# 4. SEARCH FOR RELEVANT POLICY CHUNKS
# --------------------------------------------------

def search_policy(query, collection, k=3):
    """Retrieve the k most similar policy chunks for a customer query."""

    # Load the model if it has not already been loaded.
    embedding_model = load_embedding_model()

    # Convert the customer's question into a numerical embedding.
    query_embedding = embedding_model.encode(query).tolist()

    # Find the k most similar chunks in the selected collection.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    # Display the retrieved chunks, their sources and their distances.
    for i, text in enumerate(results["documents"][0]):
        print(f"\nResult {i + 1}:")
        print(f"Policy: {text}")
        print(f"Source: {results['metadatas'][0][i]['source']}")
        print(f"Distance: {results['distances'][0][i]:.4f}")

    # Return the results so other functions can evaluate them.
    return results


# --------------------------------------------------
# 5. DEFINE THE SIMILARITY EVALUATION QUERIES
# --------------------------------------------------

# Three questions are about Nykaa support policies.
# Two questions are unrelated to the policy knowledge base.
evaluation_queries = [
    {
        "query": "How can I get my money back?",
        "expected_scope": "in_scope"
    },
    {
        "query": "How do I track my order shipment?",
        "expected_scope": "in_scope"
    },
    {
        "query": "Can I return a damaged product?",
        "expected_scope": "in_scope"
    },
    {
        "query": "What is the capital of France?",
        "expected_scope": "out_of_scope"
    },
    {
        "query": "How can I train my pet dog?",
        "expected_scope": "out_of_scope"
    }
]


# --------------------------------------------------
# 6. EVALUATE THE SIMILARITY THRESHOLD
# --------------------------------------------------

def evaluate_similarity(queries, collection):
    """Check whether each query passes the similarity threshold."""

    # Provisional threshold based on the earlier experiments.
    threshold = 0.20

    # Load the model if necessary.
    embedding_model = load_embedding_model()

    print(f"\nEvaluating collection: {collection.name}")
    print("-" * 60)

    # Evaluate each test query separately.
    for item in queries:

        # Extract the question and its expected scope.
        query = item["query"]
        expected_scope = item["expected_scope"]

        # Convert the question into an embedding.
        query_embedding = embedding_model.encode(query).tolist()

        # Retrieve only the single closest matching chunk.
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1
        )

        # ChromaDB returns cosine distance for our configured collections.
        distance = results["distances"][0][0]

        # Convert cosine distance to cosine similarity.
        similarity = 1 - distance

        # Identify the policy document associated with the best match.
        source = results["metadatas"][0][0]["source"]

        # Accept the query only if its similarity reaches the threshold.
        is_in_scope = similarity >= threshold

        # Display the evaluation results.
        print(f"\nQuery: {query}")
        print(f"Expected scope: {expected_scope}")
        print(f"Top-1 cosine distance: {distance:.4f}")
        print(f"Top-1 cosine similarity: {similarity:.4f}")
        print(f"Retrieved source: {source}")
        print(f"Threshold: {threshold:.2f}")
        print(f"Accepted as in-scope: {is_in_scope}")


# --------------------------------------------------
# 7. RUN THE DEMONSTRATION
# --------------------------------------------------

def main():
    """Build the collections and run the retrieval experiments."""

    # Generate embeddings and populate both collections.
    build_collections()

    # Demonstrate sentence-based retrieval.
    print("\n--- Sentence-based search ---")
    search_policy(
        "How can I get my money back?",
        sentence_collection
    )

    # Demonstrate fixed-size retrieval.
    print("\n--- Fixed-size search ---")
    search_policy(
        "How can I get my money back?",
        fixed_collection
    )

    # Evaluate the threshold using sentence-based chunking.
    evaluate_similarity(
        evaluation_queries,
        sentence_collection
    )

    # Evaluate the same queries using fixed-size chunking.
    evaluate_similarity(
        evaluation_queries,
        fixed_collection
    )


# Run the demonstration only when executing this file directly.
# Importing vector_store.py will not automatically build collections,
# run searches or execute the similarity evaluation.
if __name__ == "__main__":
    main()