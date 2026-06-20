"""
utils/pendo_track.py
--------------------
Server-side Pendo Track Event helper.
Sends events via HTTP POST to the Pendo Track API.
Failures are logged but never break application flow.
"""

import threading
import time
from typing import Any, Dict, Optional

import httpx

_PENDO_TRACK_URL = "https://data.pendo.io/data/track"
_PENDO_INTEGRATION_KEY = "86fbcd68-8315-4a3f-9229-01b19087de97"


def track(
    event: str,
    visitor_id: Optional[str] = None,
    account_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Send a Track Event to Pendo in a background thread so it
    never blocks or slows down the request path.
    """
    payload: Dict[str, Any] = {
        "type": "track",
        "event": event,
        "visitorId": str(visitor_id) if visitor_id is not None else "system",
        "accountId": str(account_id) if account_id is not None else "system",
        "timestamp": int(time.time() * 1000),
    }
    if properties:
        payload["properties"] = properties

    def _send() -> None:
        try:
            httpx.post(
                _PENDO_TRACK_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-pendo-integration-key": _PENDO_INTEGRATION_KEY,
                },
                timeout=5.0,
            )
        except Exception as exc:
            print(f"[pendo] Failed to send track event '{event}': {exc}")

    threading.Thread(target=_send, daemon=True).start()
