from __future__ import annotations

import streamlit as st


def ensure_app_state() -> None:
    st.session_state.setdefault("active_page", "Dashboard")
    st.session_state.setdefault("notifications_open", True)
    st.session_state.setdefault("global_search_query", "")

def cleanup_stale_session_assets(current_page: str) -> None:
    last_page = st.session_state.get("last_page")
    if last_page != current_page:
        # Page changed! Purge heavy objects
        keys_to_purge = [
            "breakthrough_zip",
            "dicgc_pdf",
            "preview_note",
            "preview_note_anniv",
            "note_params",
            "visit_zip",
            "zip_name"
        ]
        for key in list(st.session_state.keys()):
            if key in keys_to_purge:
                del st.session_state[key]
            elif any(key.startswith(prefix) for prefix in ["pdf_", "br_pdf_", "camp_post_html_"]):
                del st.session_state[key]
        st.session_state["last_page"] = current_page
