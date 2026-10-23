"""Run scripted chats against your running server and check the outcome.

    python check.py scenarios/public.json            # server on http://localhost:8000
    python check.py scenarios/public.json --url http://localhost:8001

Each scenario sends `opening`, then each of `followups`, then asks /debug/<session> what your
agent did. A scenario passes when the cancelled reservations, transfer and certificate match
`expect`, and no write tool ran on the very first user turn (policy: confirm before you act).
"""
import argparse
import json
import sys
import uuid

import httpx

WRITES = {"cancel_reservation", "send_certificate"}


def run_scenario(sc: dict, post, get) -> tuple[bool, list[str], list[dict]]:
    sid = f"check-{uuid.uuid4().hex[:8]}"
    transcript = []
    for msg in [sc["opening"], *sc["followups"]]:
        transcript.append({"role": "user", "content": msg})
        transcript.append({"role": "assistant", "content": post("/chat", {"session_id": sid, "message": msg})["reply"]})
    dbg = get(f"/debug/{sid}")
    exp, problems = sc["expect"], []
    if sorted(dbg["cancelled"]) != sorted(exp["cancelled"]):
        problems.append(f"cancelled {dbg['cancelled']} != expected {exp['cancelled']}")
    if exp.get("transferred") is True and not dbg["transferred"]:
        problems.append("expected a transfer to a human, none happened")
    certs = [c["args"].get("amount") for c in dbg["tool_calls"] if c["tool"] == "send_certificate" and c["ok"]]
    if exp.get("certificate") is None and certs:
        problems.append(f"certificate issued {certs}, expected none")
    if exp.get("certificate") is not None and certs != [exp["certificate"]]:
        problems.append(f"certificates {certs} != expected [{exp['certificate']}]")
    if any(c["tool"] in WRITES and c["turn"] < 2 for c in dbg["tool_calls"]):
        problems.append("a write tool ran on the first user turn, before any confirmation")
    return not problems, problems, transcript


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenarios")
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("-v", "--verbose", action="store_true", help="print transcripts")
    a = ap.parse_args()
    client = httpx.Client(base_url=a.url, timeout=120)
    post = lambda p, j: client.post(p, json=j).raise_for_status().json()
    get = lambda p: client.get(p).raise_for_status().json()
    failed = 0
    for sc in json.load(open(a.scenarios)):
        ok, problems, transcript = run_scenario(sc, post, get)
        failed += not ok
        print(("PASS " if ok else "FAIL ") + sc["id"] + ("" if ok else "  <- " + "; ".join(problems)))
        if a.verbose or not ok:
            for t in transcript:
                print(f"    {t['role']:9}{t['content']}")
    print(f"\n{failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
