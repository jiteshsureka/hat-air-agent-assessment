"""Thin wrapper over any OpenAI-compatible chat endpoint. Configure via .env (see .env.example)."""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
MODEL = os.getenv("LLM_MODEL", "")
_client = OpenAI(base_url=os.getenv("LLM_BASE_URL") or None, api_key=os.getenv("LLM_API_KEY", "missing"))


def complete(messages: list[dict], tools: list[dict] | None = None):
    """Return the assistant message (has .content and .tool_calls)."""
    kwargs = {"tools": tools} if tools else {}
    return _client.chat.completions.create(model=MODEL, messages=messages, temperature=0, **kwargs).choices[0].message
