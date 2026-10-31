# Import types for API response validation
from typing import Any, Literal

# Import FastAPI and Pydantic
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

# Import the existing support workflow
from support_workflow import handle_support_request

# Import tools for file handling and HTTP errors
from pathlib import Path

# Import document chunking and ChromaDB components
from chunking import (
    KNOWLEDGE_BASE_DIR,
    fixed_size_chunking,
    sentence_based_chunking,
)
from vector_store import (
    fixed_collection,
    load_embedding_model,
    sentence_collection,
)

# Import session memory functions
from conversation_memory import get_session_history

# Create the FastAPI application
app = FastAPI(title="Nykaa Support Agent API")


# Request model for customer support questions
class AskRequest(BaseModel):
    question: str = Field(min_length=1)  # Customer's question
    record_id: str | None = None  # Optional order ID


# Response model for customer support answers
class AskResponse(BaseModel):
    type: Literal["policy", "order", "blocked"]  # Response category
    result: str | dict[str, Any]  # Answer or order details


# Request model for adding a knowledge-base document
class AddDocumentRequest(BaseModel):
    filename: str = Field(min_length=1)  # Document filename
    content: str = Field(min_length=1)  # Document text


# Response model after adding a document
class AddDocumentResponse(BaseModel):
    filename: str  # Name of the added document
    chunks_added: int  # Number of indexed chunks
    message: str  # Confirmation message

# Define the POST endpoint for customer support questions
@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    # Pass the customer's question and optional order ID
    # to the existing support workflow
    result = handle_support_request(
        question=request.question,
        record_id=request.record_id
    )

    # Return the workflow result as a validated API response
    return result

# Define the POST endpoint for adding knowledge-base documents
@app.post("/add-document", response_model=AddDocumentResponse)
def add_document(request: AddDocumentRequest):

    # Accept only plain .txt filenames, preventing directory traversal
    filename = request.filename
    if Path(filename).name != filename or not filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Provide a valid .txt filename without a directory path."
        )

    # Prevent empty documents and duplicate filenames
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Document content cannot be empty.")

    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = KNOWLEDGE_BASE_DIR / filename

    if file_path.exists():
        raise HTTPException(status_code=409, detail="This document already exists.")

    # Save the document to the knowledge-base directory
    file_path.write_text(request.content, encoding="utf-8")

    # Prepare the document in the format expected by the chunking functions
    document = {
        "source": filename,
        "topic": Path(filename).stem,
        "text": request.content
    }

    # Split this document into chunks for both existing collections
    fixed_chunks = fixed_size_chunking([document])
    sentence_chunks = sentence_based_chunking([document])

    # Load the embedding model and convert each chunk into a vector
    model = load_embedding_model()

    # Add fixed-size chunks to the collection used by support answers
    if fixed_chunks:
        fixed_embeddings = model.encode(
            [chunk["text"] for chunk in fixed_chunks]
        ).tolist()

        fixed_collection.upsert(
            ids=[chunk["id"] for chunk in fixed_chunks],
            documents=[chunk["text"] for chunk in fixed_chunks],
            # Build ChromaDB metadata from the chunk's existing fields
            metadatas=[
                {
                    "source": chunk["source"],
                    "topic": chunk["topic"],
                    "chunking_strategy": chunk["chunking_strategy"]
                }
                for chunk in fixed_chunks
    ],
            embeddings=fixed_embeddings
        )

    # Also update the sentence-based collection
    if sentence_chunks:
        sentence_embeddings = model.encode(
            [chunk["text"] for chunk in sentence_chunks]
        ).tolist()

        sentence_collection.upsert(
            ids=[chunk["id"] for chunk in sentence_chunks],
            documents=[chunk["text"] for chunk in sentence_chunks],
            # Build metadata for sentence-based chunks
            metadatas=[
                {
                    "source": chunk["source"],
                    "topic": chunk["topic"],
                    "chunking_strategy": chunk["chunking_strategy"]
                }
                for chunk in sentence_chunks
            ],
            embeddings=sentence_embeddings
        )

    # Return a confirmation to the API caller
    return AddDocumentResponse(
        filename=filename,
        chunks_added=len(fixed_chunks),
        message="Document added to the knowledge base successfully."
    )

# Define a WebSocket endpoint for multi-turn customer conversations
@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):

    # Accept the client's WebSocket connection
    await websocket.accept()

    # Use the supplied session ID, or create a default session
    session_id = websocket.query_params.get("session_id", "default")
    history = get_session_history(session_id)

    try:
        # Keep the connection open for multiple messages
        while True:
            # Receive the customer's message
            question = await websocket.receive_text()

            # Store the customer's message in session memory
            history.add_user_message(question)

            # Process the message using the existing support workflow
            result = handle_support_request(question)

            # Convert the result to JSON and send it to the client
            await websocket.send_json(result)

            # Store the response in session memory
            history.add_ai_message(str(result))

    except WebSocketDisconnect:
        # Handle a client disconnect without crashing the server
        print(f"WebSocket client disconnected: session {session_id}")