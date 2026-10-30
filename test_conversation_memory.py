# Import the conversation chain and session-history store.
from conversation_memory import conversation_chain, store


# Create the first conversation session.
session_1 = {"configurable": {"session_id": "session_1"}}

# Send the first message containing an order number.
conversation_chain.invoke(
    {"question": "My order number is ORD1001"},
    config=session_1,
)

# Ask a follow-up question in the same session.
response_1 = conversation_chain.invoke(
    {"question": "What was my order number?"},
    config=session_1,
)

# Print the complete transcript for the first session.
print("=== TRANSCRIPT 1: Existing conversation ===")
for message in store["session_1"].messages:
    print(f"{message.type}: {message.content}")

# Verify that the order number is retained in the conversation.
assert "ORD1001" in response_1
assert len(store["session_1"].messages) == 4


# Create a separate conversation with a fresh session ID.
session_2 = {"configurable": {"session_id": "session_2"}}

# Send the first message in the new session.
response_2 = conversation_chain.invoke(
    {"question": "Hello, this is a new conversation."},
    config=session_2,
)

# Print the complete transcript for the fresh session.
print("\n=== TRANSCRIPT 2: Fresh conversation ===")
for message in store["session_2"].messages:
    print(f"{message.type}: {message.content}")

# Verify that the new session has no access to the previous order number.
assert "ORD1001" not in response_2
assert len(store["session_2"].messages) == 2

# Report success only after all checks pass.
print("\nPASS: Both transcripts and session isolation verified.")
