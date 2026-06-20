"""
utils/pendo.py
--------------
Pendo Track Event helpers for both client-side (Streamlit JS injection)
and server-side (HTTP POST) tracking.
"""

import json
import time
from typing import Optional

_PENDO_TRACK_URL = "https://data.pendo.io/data/track"
_PENDO_INTEGRATION_KEY = "18d45cc7-9959-4253-b4e7-bca464558030"


def inject_pendo(user=None, company=None) -> None:
    """Inject the Pendo agent snippet into the Streamlit page."""
    import streamlit.components.v1 as components
    visitor_id = str(user["id"]) if user and "id" in user else "anonymous"
    account_id = str(company["id"]) if company and "id" in company else "unknown"
    components.html(
        f"""<script>
        (function(apiKey){{
            (function(p,e,n,d,o){{var v,w,x,y,z;o=p[d]=p[d]||{{}};o._q=o._q||[];
            v=['initialize','identify','updateOptions','pageLoad','track'];
            for(w=0,x=v.length;w<x;++w)(function(m){{
                o[m]=o[m]||function(){{o._q[m===v[0]?'unshift':'push']([m].concat([].slice.call(arguments,0)));}}
            }})(v[w]);
            y=e.createElement(n);y.async=!0;
            y.src='https://cdn.pendo.io/agent/static/'+apiKey+'/pendo.js';
            z=e.getElementsByTagName(n)[0];z.parentNode.insertBefore(y,z);
            }})(window,document,'script','pendo');
            pendo.initialize({{
                visitor: {{ id: "{visitor_id}" }},
                account: {{ id: "{account_id}" }}
            }});
        }})("{_PENDO_INTEGRATION_KEY}");
        </script>""",
        height=0,
        width=0,
    )


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
