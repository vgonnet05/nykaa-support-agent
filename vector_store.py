from sentence_transformers import SentenceTransformer
import chromadb

from chunking import load_documents, sentence_based_chunking, fixed_size_chunking

# Load the local embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding dimension:", model.get_sentence_embedding_dimension())

# Load the policy documents
documents = load_documents()

# Generate chunks using both strategies
sentence_chunks = sentence_based_chunking(documents)
fixed_chunks = fixed_size_chunking(documents)

# Convert sentence-based chunk text into embeddings
sentence_embeddings = model.encode(
    [chunk["text"] for chunk in sentence_chunks]
)

# Convert fixed-size chunk text into embeddings
fixed_embeddings = model.encode(
    [chunk["text"] for chunk in fixed_chunks]
)

# Display the results
print("Sentence-based chunks:", len(sentence_chunks))
print("Sentence-based embeddings:", sentence_embeddings.shape)

print("Fixed-size chunks:", len(fixed_chunks))
print("Fixed-size embeddings:", fixed_embeddings.shape)

# Create a persistent ChromaDB client
client = chromadb.PersistentClient(path="./chroma_db")

# Create or retrieve the sentence-based collection
#sentence_collection = client.get_or_create_collection(
#    name="sentence_chunks"
#)

# Delete existing collections so they can be recreated with cosine distance
client.delete_collection(name="sentence_chunks")
client.delete_collection(name="fixed_size_chunks")

# Create collections using cosine distance
sentence_collection = client.create_collection(
    name="sentence_chunks",
    metadata={"hnsw:space": "cosine"}
)

fixed_collection = client.create_collection(
    name="fixed_size_chunks",
    metadata={"hnsw:space": "cosine"}
)

# Store sentence-based chunks and their embeddings
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

# Create or retrieve the fixed-size collection
#fixed_collection = client.get_or_create_collection(
#    name="fixed_size_chunks"
#)

# Store fixed-size chunks and their embeddings
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

# Verify the stored record counts
print("Sentence collection records:", sentence_collection.count())
print("Fixed-size collection records:", fixed_collection.count())

# Function to search for relevant policy chunks based on a customer query
def search_policy(query, collection, k=3):
    # Convert the customer query into an embedding
    query_embedding = model.encode(query).tolist()

    # Search for the most similar chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    # Display the retrieved chunks
    for i, text in enumerate(results["documents"][0]):
        print(f"\nResult {i + 1}:")
        print(f"Policy: {text}")
        print(f"Source: {results['metadatas'][0][i]['source']}")
        print(f"Distance: {results['distances'][0][i]:.4f}")

    return results

print("\n--- Sentence-based search ---")
search_policy(
    "How can I get my money back?",
    sentence_collection
)

print("\n--- Fixed-size search ---")

search_policy(
    "How can I get my money back?",
    fixed_collection
)


# Function to evaluate the similarity of search results
def evaluate_similarity(queries, collection):

    # Provisional threshold based on the current evaluation results
    threshold = 0.20

    print(f"\nEvaluating collection: {collection.name}")
    print("-" * 60)

    # Process each evaluation test case
    for item in queries:

        # Extract the query and its expected scope
        query = item["query"]
        expected_scope = item["expected_scope"]

        # Convert the query into an embedding
        query_embedding = model.encode(query).tolist()

        # Retrieve the single closest matching chunk
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1
        )

        # Extract cosine distance and convert it to similarity
        distance = results["distances"][0][0]
        similarity = 1 - distance

        # Retrieve the source document
        source = results["metadatas"][0][0]["source"]

        # Decide whether the query passes the similarity threshold
        is_in_scope = similarity >= threshold

        # Print the evaluation results
        print(f"\nQuery: {query}")
        print(f"Expected scope: {expected_scope}")
        print(f"Top-1 cosine distance: {distance:.4f}")
        print(f"Top-1 cosine similarity: {similarity:.4f}")
        print(f"Retrieved source: {source}")
        print(f"Threshold: {threshold:.2f}")
        print(f"Accepted as in-scope: {is_in_scope}")

# Define evaluation queries for testing the search functionality
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


# Evaluate the sentence-based collection
evaluate_similarity(evaluation_queries, sentence_collection)

# Evaluate the fixed-size collection
evaluate_similarity(evaluation_queries, fixed_collection)