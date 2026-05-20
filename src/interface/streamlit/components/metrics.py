import streamlit as st

def render_metric_card(label: str, value: str, delta: str = None, color: str = "primary"):
    """
    Renders a premium metric card using HTML/CSS.
    """
    st.markdown(f"""
        <div class="metric-card" style="border-bottom-color: var(--{color});">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {f'<div style="color: var(--success); font-size: 0.8rem;">↑ {delta}</div>' if delta else ''}
        </div>
    """, unsafe_allow_html=True)

def render_metric_row(metrics: list[dict]):
    cols = st.columns(len(metrics))
    for i, m in enumerate(metrics):
        with cols[i]:
            render_metric_card(
                m.get("label"), 
                m.get("value"), 
                m.get("delta"),
                m.get("color", "primary")
            )
