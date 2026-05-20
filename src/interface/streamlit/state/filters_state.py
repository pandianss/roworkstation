from __future__ import annotations

import streamlit as st


def ensure_filter_state() -> None:
    st.session_state.setdefault("task_filters", {"status": "All", "priority": "All", "search": ""})
    st.session_state.setdefault("mis_filters", {"date": None, "sols": []})
