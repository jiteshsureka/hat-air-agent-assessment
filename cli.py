"""Chat with your running server from the terminal:  python cli.py"""
import uuid

import httpx

sid = f"cli-{uuid.uuid4().hex[:6]}"
print(f"session {sid}. Ctrl-C to quit.")
while True:
    msg = input("you> ")
    print("bot>", httpx.post("http://localhost:8000/chat", json={"session_id": sid, "message": msg}, timeout=120).json()["reply"])
