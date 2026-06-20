"""
utils/pendo.py
--------------
Server-side Pendo Track Event helper.
Sends events to the Pendo Track API via HTTP POST in a background thread
so tracking never blocks the main application flow.
"""

import threading
import time

import httpx

_PENDO_TRACK_URL = "https://data.pendo.io/data/track"
_PENDO_INTEGRATION_KEY = "c031e3b8-ccf2-4ac6-9d29-ca3aee0dd95b"


def track_event(event, visitor_id, account_id, properties=None):
    """Fire a Pendo Track Event (non-blocking)."""
    payload = {
        "type": "track",
        "event": event,
        "visitorId": str(visitor_id),
        "accountId": str(account_id),
        "timestamp": int(time.time() * 1000),
    }
    if properties:
        payload["properties"] = properties

    def _send():
        try:
            with httpx.Client(timeout=5.0) as client:
                client.post(
                    _PENDO_TRACK_URL,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-pendo-integration-key": _PENDO_INTEGRATION_KEY,
                    },
                )
        except Exception as exc:
            print(f"[pendo] Failed to track '{event}': {exc}")

    threading.Thread(target=_send, daemon=True).start()
