from fastapi import FastAPI
from pydantic import BaseModel

from . import agent
from .session import Session

app = FastAPI()
SESSIONS: dict[str, Session] = {}


class ChatIn(BaseModel):
    session_id: str
    message: str


@app.post("/chat")
def chat(body: ChatIn) -> dict:
    s = SESSIONS.setdefault(body.session_id, Session(body.session_id))
    s.user_turns += 1
    return {"reply": agent.respond(s, body.message)}


@app.get("/debug/{session_id}")
def debug(session_id: str) -> dict:
    """Used by check.py. Reports what the agent did through the toolbox."""
    s = SESSIONS.get(session_id)
    if s is None:
        return {"tool_calls": [], "cancelled": [], "transferred": False}
    return {"tool_calls": s.toolbox.log, "cancelled": s.toolbox.cancelled(), "transferred": s.toolbox.transferred}
