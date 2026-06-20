"""
utils/pendo.py
--------------
Pendo SDK integration for the Streamlit app.
Injects the Pendo install snippet and lifecycle calls (initialize, identify,
clearSession) into the parent browser window via streamlit.components.v1.html().
"""

import json

import streamlit as st
import streamlit.components.v1 as components

_PENDO_API_KEY = '18d45cc7-9959-4253-b4e7-bca464558030'


def inject_pendo(user=None, company=None):
    """
    Inject the Pendo SDK snippet and the appropriate lifecycle call.

    Args:
        user: User dict (id, email, role, company_id, created_at) or None for anonymous.
        company: Company dict (id, name, website, scraping_enabled, created_at) or None.
    """
    clear_session_js = ''
    if st.session_state.pop('pendo_clear_session', False):
        clear_session_js = (
            'if (w.pendo && w.pendo.clearSession) { w.pendo.clearSession(); }\n'
            '        w._pendoInitialized = false;'
        )

    lifecycle_js = ''
    if user:
        visitor_data = {
            'id': user['id'],
            'email': user.get('email', ''),
            'companyId': user.get('company_id', ''),
            'role': user.get('role', ''),
            'createdAt': user.get('created_at', ''),
        }
        account_data = {
            'id': user.get('company_id', ''),
        }
        if company:
            account_data['name'] = company.get('name', '')
            account_data['website'] = company.get('website', '')
            account_data['scrapingEnabled'] = bool(company.get('scraping_enabled', 0))
            account_data['createdAt'] = company.get('created_at', '')

        identify_json = json.dumps({'visitor': visitor_data, 'account': account_data})
        lifecycle_js = f'w.pendo.identify({identify_json});'

    html_content = f"""
    <script>
    (function() {{
        var w = window.parent || window;

        // Load Pendo agent script (only once per browser session)
        if (!w._pendoScriptLoaded) {{
            w._pendoScriptLoaded = true;
            (function(apiKey) {{
                (function(p,e,n,d,o) {{
                    var v,w2,x,y,z;
                    o=p[d]=p[d]||{{}};o._q=o._q||[];
                    v=['initialize','identify','updateOptions','pageLoad','track','trackAgent'];
                    for(w2=0,x=v.length;w2<x;++w2)(function(m){{
                        o[m]=o[m]||function(){{o._q[m===v[0]?'unshift':'push']([m].concat([].slice.call(arguments,0)));}};
                    }})(v[w2]);
                    y=e.createElement(n);y.async=!0;
                    y.src='https://cdn.pendo.io/agent/static/'+apiKey+'/pendo.js';
                    z=e.getElementsByTagName(n)[0];z.parentNode.insertBefore(y,z);
                }})(w,w.document,'script','pendo');
            }})('{_PENDO_API_KEY}');
        }}

        // Handle session clear (on logout)
        {clear_session_js}

        // Initialize with anonymous visitor (once, or after clearSession reset)
        if (!w._pendoInitialized) {{
            w._pendoInitialized = true;
            w.pendo.initialize({{ visitor: {{ id: '' }} }});
        }}

        // Identify signed-in user
        {lifecycle_js}
    }})();
    </script>
    """

    components.html(html_content, height=0)
