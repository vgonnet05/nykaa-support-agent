# Import FastAPI's test client and the application
from fastapi.testclient import TestClient
from api import app

# Create a test client
client = TestClient(app)

# Simulate a client connecting and disconnecting before sending a message
with client.websocket_connect("/ws/chat?session_id=disconnect-test"):
    pass

print("First client disconnected.")

# Verify that a second client can still connect and exchange messages
with client.websocket_connect("/ws/chat?session_id=second-client") as websocket:
    websocket.send_text("What is the refund policy?")
    response = websocket.receive_json()
    print("Second client response type:", response["type"])

print("Second client completed successfully.")