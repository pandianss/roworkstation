from __future__ import annotations

import streamlit as st
import pandas as pd
import io
from src.application.services.mail_merge_service import MailMergeService
from src.interface.streamlit.components.primitives import render_action_bar


def render() -> None:
    service = MailMergeService()
    render_action_bar("Mail Merge Engine", ["Bulk Generation", "Excel Binding", "WeasyPrint PDF"])
    
    st.info("💡 **How it works:** Upload an Excel file with columns matching your template variables (e.g., {{NAME}}, {{ADDRESS}}).")
    
    col_t, col_d = st.columns(2)
    
    with col_t:
        st.markdown("#### 1. Define HTML Template")
        template_text = st.text_area("HTML Content", value="""
<div style="font-family: Arial; padding: 40px;">
    <h1>Notice to {{NAME}}</h1>
    <p>Dear {{NAME}},</p>
    <p>This is regarding your account with SOL <strong>{{BRANCH}}</strong>.</p>
    <p>Please visit the branch regarding {{SUBJECT}}.</p>
    <br>
    <p>Regional Manager,<br>Dindigul</p>
</div>
        """, height=300)
        
    with col_d:
        st.markdown("#### 2. Upload Data Source")
        data_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])
        if data_file:
            df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button("🚀 Process Bulk Merge"):
                with st.spinner("Generating high-fidelity PDFs..."):
                    try:
                        pdfs = service.process_merge(template_text, df)
                        st.success(f"Generated {len(pdfs)} documents successfully!")
                        
                        # In a real app, we'd zip them or offer individual downloads
                        st.download_button("Download All (Zipped)", data=b"placeholder", file_name="merged_docs.zip")
                    except Exception as e:
                        st.error(f"Merge failed: {str(e)}")
                        st.info("Hint: Ensure all {{VARIABLE}} names match Excel column headers exactly.")
