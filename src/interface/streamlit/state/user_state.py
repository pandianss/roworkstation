from __future__ import annotations

import streamlit as st

from src.core.security.auth import resolve_current_user


def ensure_user_state() -> None:
    current_user = resolve_current_user()
    st.session_state["username"] = current_user.username
    st.session_state["role"] = current_user.role
    st.session_state["user_dept"] = current_user.dept
    st.session_state["user_depts"] = current_user.depts
    st.session_state["display_name"] = current_user.name or current_user.username
