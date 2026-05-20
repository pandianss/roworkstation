from __future__ import annotations

from typing import Any
import io

import pandas as pd
import plotly.express as px
import streamlit as st


def render_status_badge(text: str, level: str = "low") -> None:
    st.markdown(f'<span class="status-pill status-{level}">{text}</span>', unsafe_allow_html=True)


def render_metric_cards(metrics: dict[str, str | int | float]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value) in zip(columns, metrics.items()):
        column.metric(label, value)


def render_filter_panel(title: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="glass-panel">
            <div class="section-title"><strong>{title}</strong></div>
            <div class="section-kicker">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_bar(title: str, actions: list[str]) -> None:
    import base64
    import os
    logo_html = ""
    logo_path = "src/assets/2026logo_min.svg"
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            logo_html = f'<img src="data:image/svg+xml;base64,{encoded}" style="height: 35px; margin-right: 15px; vertical-align: middle;" />'
        except Exception:
            pass

    items = "".join([f"<span class='status-pill status-low' style='margin-left: 8px; background: rgba(59, 130, 246, 0.1); color: #60a5fa;'>{action}</span>" for action in actions])
    st.markdown(
        f"""
        <div class="top-bar-container" style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 700; color: #f8fafc;">
                {logo_html}
                <span>{title}</span>
            </div>
            <div style="display: flex; align-items: center;">
                {items}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


from src.core.utils.number_utils import format_indian_number

def render_data_table(frame: pd.DataFrame, title: str, export_name: str) -> None:
    # Optimized column formatting
    display_df = frame.copy()
    for col in display_df.columns:
        if pd.api.types.is_datetime64_any_dtype(display_df[col]):
            display_df[col] = display_df[col].dt.strftime('%d.%m.%Y')
        elif pd.api.types.is_numeric_dtype(display_df[col]):
            col_upper = str(col).upper()
            if any(k in col_upper for k in ["AMOUNT", "BALANCE", "ADVANCE", "DEPOSIT", "VALUE", "BUDGET", "CASH", "NPA", "BUS"]):
                # map() is generally faster than apply() for element-wise operations
                display_df[col] = display_df[col].map(lambda x: format_indian_number(x) if pd.notnull(x) else x)

    st.markdown(
        f"""
        <div class="glass-panel" style="margin-bottom: 0.75rem;">
            <div class="section-title"><strong>{title}</strong></div>
            <div class="table-count">{len(display_df)} row(s)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Optimized dataframe rendering with height and container width
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=min(420, (len(display_df) + 1) * 35 + 40))
    
    @st.cache_data(ttl=300) # Cache the excel generation for 5 minutes
    def get_excel_bytes(df_dict: dict):
        df = pd.DataFrame.from_dict(df_dict)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        return buffer.getvalue()
        
    excel_bytes = get_excel_bytes(display_df.to_dict('records'))
    st.download_button("📥 Export to Excel", data=excel_bytes, file_name=export_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def render_chart_container(frame: pd.DataFrame, x: str, y: str | list[str], title: str, kind: str = "line", color: str | None = None):
    if frame.empty:
        st.info("No data available.")
        return
    if kind == "bar":
        figure = px.bar(frame, x=x, y=y, color=color, title=title)
    elif kind == "pie":
        figure = px.pie(frame, names=x, values=y, title=title, hole=0.45)
    else:
        figure = px.line(frame, x=x, y=y, color=color, title=title, markers=True)
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_dark",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(figure, use_container_width=True)


def render_premium_metrics(metrics: dict[str, Any]) -> None:
    """Renders glassmorphic metric cards for a premium feel with Indian formatting."""
    cols = st.columns(len(metrics))
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i]:
            if isinstance(value, (int, float)):
                # Heuristic: Use symbols for financial metrics
                is_financial = any(k in label.upper() for k in ["ADVANCE", "DEPOSIT", "CASH", "LIMIT", "NPA", "₹"])
                display_val = format_indian_number(value, include_symbol=is_financial)
            else:
                display_val = str(value)
                
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{display_val}</div>
                </div>
            """, unsafe_allow_html=True)


def render_section_divider() -> None:
    """Renders a premium gold-gradient divider."""
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)


def render_info_banner(title: str, message: str, icon: str = "✨") -> None:
    """Renders a premium glassmorphic announcement banner."""
    st.markdown(f"""
        <div class="glass-card-gold">
            <div style="display: flex; align-items: flex-start; gap: 1rem;">
                <div style="font-size: 1.5rem;">{icon}</div>
                <div>
                    <div class="text-gold" style="font-size: 1rem; margin-bottom: 4px;">{title}</div>
                    <div style="color: var(--text-secondary); font-size: 0.9rem;">{message}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
