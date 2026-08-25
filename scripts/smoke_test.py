"""Local MVP smoke test against running API."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8001"


def call(method: str, path: str, body: dict | None = None, token: str | None = None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            raw = res.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        raise SystemExit(f"{method} {path} -> {e.code}: {detail}") from e


def main() -> None:
    health = call("GET", "/health")
    assert health.get("status") == "ok", health

    email = f"smoke{int(time.time())}@test.com"
    token = call(
        "POST",
        "/api/auth/register",
        {"email": email, "password": "secret12", "display_name": "Smoke"},
    )["access_token"]

    home = call("GET", "/api/home", token=token)
    assert home["user"]["display_name"] == "Smoke"
    assert len(home["mission"]["tasks"]) == 4
    print("home ok", "due", home["due_count"])

    vocab = call("GET", "/api/vocab?hsk_level=1&limit=3", token=token)
    assert len(vocab) >= 1
    print("vocab ok", len(vocab))

    cards = call("GET", "/api/cards/due", token=token)
    assert len(cards) >= 1
    reviewed = call("POST", f"/api/cards/{cards[0]['id']}/review", {"rating": "good"}, token)
    assert reviewed["reps"] >= 1
    print("flashcard ok")

    listen = call("GET", "/api/listening/next", token=token)
    assert len(listen["options"]) == 4
    call("POST", "/api/listening/complete?correct=true", token=token)
    print("listening ok")

    scenarios = call("GET", "/api/scenarios?track=work", token=token)
    assert len(scenarios) == 5
    session = call("POST", "/api/roleplay/sessions", {"scenario_id": scenarios[0]["id"]}, token)
    updated = call(
        "POST",
        f"/api/roleplay/sessions/{session['id']}/message",
        {"message": "老板，因为供应商还没到货，订单可能会延期两天。"},
        token,
    )
    assert updated.get("scores")
    assert len(updated["messages"]) >= 3
    print("roleplay ok keys", list(updated["scores"].keys()))
    print("SMOKE PASS")


if __name__ == "__main__":
    main()
