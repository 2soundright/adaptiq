"""
utils/pendo.py
--------------
Pendo Track Event helpers for both client-side (Streamlit JS injection)
and server-side (HTTP POST) tracking.
"""

import json
import time
from typing import Optional


def track_event(event_name: str, properties: Optional[dict] = None) -> None:
    """Inject a pendo.track() call via JavaScript in a Streamlit page."""
    import streamlit.components.v1 as components

    props_json = json.dumps(properties or {})
    components.html(
        f"""<script>
        (function() {{
            try {{
                var p = (window.parent && window.parent.pendo) || window.pendo;
                if (p && typeof p.track === 'function') {{
                    p.track("{event_name}", {props_json});
                }}
            }} catch(e) {{ }}
        }})();
        </script>""",
        height=0,
        width=0,
    )


_PENDO_TRACK_URL = "https://data.pendo.io/data/track"
_PENDO_INTEGRATION_KEY = "4e308391-5688-48ad-b1a2-f121c7565c18"


def track_event_server(
    event_name: str,
    visitor_id: Optional[str] = None,
    account_id: Optional[str] = None,
    properties: Optional[dict] = None,
) -> None:
    """Send a Pendo Track Event via HTTP POST (server-side)."""
    import httpx

    payload = {
        "type": "track",
        "event": event_name,
        "visitorId": str(visitor_id) if visitor_id else "system",
        "accountId": str(account_id) if account_id else "system",
        "timestamp": int(time.time() * 1000),
        "properties": properties or {},
    }
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
        print(f"[pendo] Failed to send track event '{event_name}': {exc}")
