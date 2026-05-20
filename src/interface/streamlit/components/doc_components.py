import streamlit as st

def render_wizard_tile(icon: str, title: str, description: str, key: str) -> bool:
    """Renders a premium, interactive tile using the global design system."""
    st.markdown(
        f"""
        <div class="launcher-tile">
            <div style="font-size: 2.5rem; margin-bottom: 12px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));">{icon}</div>
            <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.25rem; color: #f8fafc; margin-bottom: 8px;">{title}</div>
            <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5; font-weight: 400;">{description}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    return st.button(f"Launch {title}", key=f"btn_{key}", use_container_width=True)

def render_document_card(doc_type: str, subject: str, reference: str, date: str, author: str, key: str):
    """Renders a high-density archive card with action buttons."""
    with st.container(border=True):
        col_main, col_actions = st.columns([4, 1.2])
        
        with col_main:
            # Badge logic
            type_color = "#3b82f6" # Default blue
            if "circular" in doc_type.lower(): type_color = "#8b5cf6" # Purple
            if "office note" in doc_type.lower(): type_color = "#10b981" # Green
            
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <span class="status-pill status-{'high' if 'circular' in doc_type.lower() else ('med' if 'office note' in doc_type.lower() else 'low')}">
                        {doc_type}
                    </span>
                    <span style="font-family: 'Outfit', sans-serif; font-size: 0.8rem; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">{reference}</span>
                </div>
                <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.15rem; color: #f1f5f9; margin-bottom: 4px;">{subject}</div>
                <div style="font-size: 0.85rem; color: #94a3b8;">
                    <span style="color: #60a5fa; font-weight: 700;">{date}</span> &middot; <span style="opacity: 0.8;">{author}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col_actions:
            # Compact buttons
            c1, c2 = st.columns(2)
            pdf_btn = c1.button("📄", key=f"pdf_{key}", help="Generate/Download PDF")
            edit_btn = c2.button("✏️", key=f"edit_{key}", help="Edit Draft")
            del_btn = st.button("🗑️", key=f"del_{key}", help="Delete Entry", use_container_width=True)
            
            return pdf_btn, edit_btn, del_btn
