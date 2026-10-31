# Import FastAPI's test client and our application
from fastapi.testclient import TestClient
from api import app

# Create a test client for the application
client = TestClient(app)

# Open a WebSocket connection with a session ID
with client.websocket_connect("/ws/chat?session_id=test-session") as websocket:

    # Send the first customer question
    websocket.send_text("What is the return policy?")

    # Receive and display the first response
    response1 = websocket.receive_json()
    print("Reply 1:", response1)

    # Send a second question on the same connection
    websocket.send_text("What is the refund policy?")

    # Receive and display the second response
    response2 = websocket.receive_json()
    print("Reply 2:", response2)

# Confirm the test connection closed normally
print("WebSocket disconnected cleanly")