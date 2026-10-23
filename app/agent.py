"""THE PART YOU BUILD.

respond() is called once per user message. It must return the reply text.

What you have to work with:
  session.history   list you can keep OpenAI-style messages in (yours to manage)
  session.toolbox   .schemas() -> tool definitions for the LLM, .call(name, args) -> JSON string
  llm.complete()    one LLM call; returns a message with .content and .tool_calls
  policy/policy.md  the company policy. Read it from disk (see README).
"""
from .session import Session


def respond(session: Session, user_message: str) -> str:
    raise NotImplementedError("build me")
