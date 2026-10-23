"""Tools the agent may call. Backed by data/db.json (a fictional airline).

Derived from the airline domain of tau2-bench (MIT, Sierra Research):
https://github.com/sierra-research/tau2-bench

IMPORTANT: like the original, the write tools do NOT check business rules.
Deciding whether an action is allowed is the agent's job.
"""
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "db.json"
NOW = datetime(2024, 5, 15, 15, 0)  # "current time" in the policy (EST)

_DB = None


def _db() -> dict:
    global _DB
    if _DB is None:
        _DB = json.loads(DB_PATH.read_text())
    return _DB


SCHEMAS = [
    {"name": "get_user_details", "description": "Get a user's profile: membership level, payment methods, reservation ids.",
     "parameters": {"type": "object", "properties": {"user_id": {"type": "string", "description": "e.g. 'sara_doe_496'"}}, "required": ["user_id"]}},
    {"name": "get_reservation_details", "description": "Get a reservation: flights, cabin, passengers, payments, created_at, insurance.",
     "parameters": {"type": "object", "properties": {"reservation_id": {"type": "string", "description": "e.g. '8JX2WO'"}}, "required": ["reservation_id"]}},
    {"name": "get_flight_status", "description": "Status of one flight on one date: available, delayed, on time, flying, landed or cancelled.",
     "parameters": {"type": "object", "properties": {"flight_number": {"type": "string"}, "date": {"type": "string", "description": "YYYY-MM-DD"}}, "required": ["flight_number", "date"]}},
    {"name": "cancel_reservation", "description": "WRITE. Cancel a whole reservation and refund all payments. Performs no eligibility checks.",
     "parameters": {"type": "object", "properties": {"reservation_id": {"type": "string"}}, "required": ["reservation_id"]}},
    {"name": "send_certificate", "description": "WRITE. Issue a travel certificate (compensation) to a user. Performs no eligibility checks.",
     "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}, "amount": {"type": "integer"}}, "required": ["user_id", "amount"]}},
    {"name": "transfer_to_human_agents", "description": "Hand the conversation to a human, with a summary of the issue.",
     "parameters": {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}},
]
WRITE_TOOLS = {"cancel_reservation", "send_certificate"}


class ToolBox:
    """One instance per chat session. Changes live in this object, not in db.json."""

    def __init__(self, turn=lambda: 0):
        self.log: list[dict] = []  # every call, in order; read by /debug and check.py
        self.transferred = False
        self._turn = turn
        self._res: dict[str, dict] = {}
        self._users: dict[str, dict] = {}

    # --- what you hand to the LLM -------------------------------------------------
    def schemas(self) -> list[dict]:
        """OpenAI-style tool definitions."""
        return [{"type": "function", "function": s} for s in SCHEMAS]

    def call(self, name: str, args: dict) -> str:
        """Run a tool, return a JSON string. Never raises: errors come back as {"error": ...}."""
        try:
            result = getattr(self, name)(**args)
            out = {"result": result}
        except Exception as e:  # unknown tool, bad args, not found...
            out = {"error": f"{type(e).__name__}: {e}"}
        self.log.append({"turn": self._turn(), "tool": name, "args": args, "ok": "error" not in out})
        return json.dumps(out)

    # --- tools --------------------------------------------------------------------
    def _reservation(self, rid: str) -> dict:
        if rid in self._res:
            return self._res[rid]
        if rid not in _db()["reservations"]:
            raise ValueError(f"reservation {rid} not found")
        return deepcopy(_db()["reservations"][rid])

    def _user(self, uid: str) -> dict:
        if uid in self._users:
            return self._users[uid]
        if uid not in _db()["users"]:
            raise ValueError(f"user {uid} not found")
        return deepcopy(_db()["users"][uid])

    def get_user_details(self, user_id: str) -> dict:
        return self._user(user_id)

    def get_reservation_details(self, reservation_id: str) -> dict:
        return self._reservation(reservation_id)

    def get_flight_status(self, flight_number: str, date: str) -> str:
        flights = _db()["flights"]
        if flight_number not in flights or date not in flights[flight_number]["dates"]:
            raise ValueError(f"flight {flight_number} on {date} not found")
        return flights[flight_number]["dates"][date]["status"]

    def cancel_reservation(self, reservation_id: str) -> dict:
        r = self._reservation(reservation_id)
        r["payment_history"] += [{"payment_id": p["payment_id"], "amount": -p["amount"]} for p in r["payment_history"]]
        r["status"] = "cancelled"
        self._res[reservation_id] = r
        return r

    def send_certificate(self, user_id: str, amount: int) -> str:
        u = self._user(user_id)
        cert_id = f"certificate_{len([k for k in u['payment_methods'] if k.startswith('certificate_')]) + 1000001}"
        u["payment_methods"][cert_id] = {"source": "certificate", "id": cert_id, "amount": amount}
        self._users[user_id] = u
        return f"Certificate {cert_id} added to user {user_id} with amount {amount}."

    def transfer_to_human_agents(self, summary: str) -> str:
        self.transferred = True
        return "Transfer successful"

    # --- used by /debug and check.py ---------------------------------------------
    def cancelled(self) -> list[str]:
        return sorted(k for k, v in self._res.items() if v.get("status") == "cancelled")

    def certificates(self) -> list[dict]:
        return [c for c in self.log if c["tool"] == "send_certificate" and c["ok"]]
