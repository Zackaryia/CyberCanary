import time
from httpx_ws import connect_ws

import httpx

# def connect_ws(url):
#     """Creates and returns a WebSocket connection."""
#     try:
#         ws = create_connection(url)
#         print(f"Connected to {url}")
#         return ws
#     except Exception as e:
#         print(f"WebSocket connection error: {e}")
#         return None

def x():
    with connect_ws("wss://jetstream1.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post&cursor=1740098738545575") as ws:
        while True:
            message = ws.receive_text()
            print(message)

if __name__ == "__main__":
    x()