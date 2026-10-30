"""
Task 8: Conversation Memory

Demonstrates:
1. Remembering earlier messages within the same session.
2. Keeping different conversation sessions isolated.

This initial implementation tests LangChain's memory mechanism
without requiring an external LLM or API key.
"""

# Stores conversation messages in memory.
from langchain_core.chat_history import InMemoryChatMessageHistory

# Creates a runnable chain that manages conversation history.
from langchain_core.runnables.history import RunnableWithMessageHistory

# Defines a simple runnable for testing the memory mechanism.
from langchain_core.runnables import RunnableLambda


# Dictionary holding a separate message history for each session ID.
# Example: "session_1" and "session_2" have independent histories.
store = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """
    Return the message history for a session.

    If the session is new, create an empty history.
    If it already exists, return its existing history.
    """
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()

    return store[session_id]


def echo_with_history(inputs: dict) -> str:
    """
    Test runnable that receives the current input and conversation history.

    It returns the history alongside the latest message so we can
    verify that previous messages are available to the chain.
    """
    history = inputs.get("history", [])
    question = inputs["question"]

    # Convert stored messages into readable text for inspection.
    previous_messages = "\n".join(
        f"{message.type}: {message.content}"
        for message in history
    )

    return (
        f"Previous conversation:\n{previous_messages}\n"
        f"Current question: {question}"
    )


# Wrap the test runnable with automatic conversation-history management.
conversation_chain = RunnableWithMessageHistory(
    # Runnable that processes the current question and history.
    RunnableLambda(echo_with_history),

    # Function that retrieves the correct history for each session.
    get_session_history,

    # Input key containing the user's current message.
    input_messages_key="question",

    # Input key through which previous conversation messages are supplied.
    history_messages_key="history",
)
