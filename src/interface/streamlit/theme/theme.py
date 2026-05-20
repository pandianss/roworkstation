from __future__ import annotations

import streamlit as st

from src.core.paths import project_path


def apply_theme() -> None:
    css_path = project_path("src", "interface", "streamlit", "theme", "styles.css")
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
