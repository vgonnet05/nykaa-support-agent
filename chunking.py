# Import Path to work with file and directory paths
from pathlib import Path

# Define the folder containing the knowledge-base documents
KNOWLEDGE_BASE_DIR = Path("knowledge_base")

#Function to load policy documents
def load_documents():
    # Create an empty list to store the documents we load
    documents = []

    # Find all .txt files and sort them for consistent processing
    for file_path in sorted(KNOWLEDGE_BASE_DIR.glob("*.txt")):

        # Read the complete text from the current file
        text = file_path.read_text(encoding="utf-8")

        # Store the document content along with its source and topic
        documents.append({
            "source": file_path.name,  # Original filename
            "topic": file_path.stem,   # Filename without the .txt extension
            "text": text               # Complete document content
        })

    # Return the list of loaded documents to the caller
    return documents

# Function to create sentence-based chunks
def sentence_based_chunking(documents):
    # Create an empty list to store all generated chunks
    chunks = []

    # Process each policy document in the documents list
    for document in documents:

        # Extract the document's text and split it into a list of sentences
        sentences = [
            sentence.strip()
            for sentence in document["text"].split(". ")
            if sentence.strip()
        ]

        # Process the sentences in groups of three
        for i in range(0, len(sentences), 3):

            # Select up to three sentences for the current chunk
            chunk_sentences = sentences[i:i + 3]

            # Combine the selected sentences into a single string
            chunk_text = ". ".join(chunk_sentences)

            # Create a dictionary representing one chunk
            # Preserve the original document's source and topic
            chunk = {
                "id": f"sentence_{document['topic']}_{i // 3 + 1:03d}",
                "text": chunk_text,
                "source": document["source"],
                "topic": document["topic"],
                "chunking_strategy": "sentence_based"
            }

            # Add the newly created chunk dictionary to the chunks list
            chunks.append(chunk)

    # Return the complete list of chunks to the caller
    return chunks

#   Function to create fixed-size chunks with overlap
def fixed_size_chunking(documents):
    # Define the maximum chunk size and overlap in characters
    chunk_size = 200
    overlap = 40

    # Create an empty list to store all chunks
    chunks = []

    # Process each policy document
    for document in documents:
        # Extract the complete text of the current document
        text = document["text"]

        # Start from the first character
        start = 0

        # Track the chunk number for this document
        chunk_number = 1

        # Continue until we reach the end of the text
        while start < len(text):
            # Calculate the ending position of the current chunk
            end = start + chunk_size

            # Extract up to 200 characters
            chunk_text = text[start:end]

            # Create a dictionary representing this chunk
            chunk = {
                "id": f"fixed_{document['topic']}_{chunk_number:03d}",
                "text": chunk_text,
                "source": document["source"],
                "topic": document["topic"],
                "chunking_strategy": "fixed_size"
            }

            # Add the chunk to the list
            chunks.append(chunk)

            # Move forward by 160 characters to maintain 40-character overlap
            start += chunk_size - overlap

            # Increment the chunk number
            chunk_number += 1

    # Return all generated chunks
    return chunks

# Run this section only when chunking.py is executed directly
if __name__ == "__main__":
    documents = load_documents()

    sentence_chunks = sentence_based_chunking(documents)
    fixed_chunks = fixed_size_chunking(documents)

    print(f"Documents loaded: {len(documents)}")
    print(f"Sentence-based chunks: {len(sentence_chunks)}")
    print(f"Fixed-size chunks: {len(fixed_chunks)}")

    print("\nFirst sentence-based chunk:")
    print(sentence_chunks[0])

    print("\nFirst fixed-size chunk:")
    print(fixed_chunks[0])

    print("\nValidation:")

    print(
    "Sentence-based IDs are unique:",
    len({chunk["id"] for chunk in sentence_chunks}) == len(sentence_chunks)
    )

    print(
    "Fixed-size IDs are unique:",
    len({chunk["id"] for chunk in fixed_chunks}) == len(fixed_chunks)
    )

    print(
    "Largest fixed-size chunk:",
    max(len(chunk["text"]) for chunk in fixed_chunks)
    )