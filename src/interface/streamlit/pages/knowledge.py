from __future__ import annotations

import pandas as pd
import streamlit as st

from src.application.services.hub_service import KnowledgeHubService
from src.interface.streamlit.components.primitives import render_action_bar, render_data_table

@st.cache_resource
def get_hub_service():
    return KnowledgeHubService()

def render() -> None:
    hub_service = get_hub_service()

    render_action_bar("Policy & Product Archive", ["Circulars", "Product Directory", "Manuals"])
    
    tabs = st.tabs(["📂 Regional Circulars", "🏦 Bank Products"])

    # 1. Document Archive (Circulars)
    with tabs[0]:
        st.subheader("Regional Circular Archive")
        st.info("Browse and search the history of regional office circulars by category.")
        
        category = st.selectbox("Category Filter", ["All", "Operations", "Retail", "HR", "IT", "Recovery"])
        filter_cat = None if category == "All" else category
        circulars = hub_service.list_circulars(category=filter_cat)
        
        if circulars:
            render_data_table(pd.DataFrame(circulars), f"{category} Archive", "circular_archive.xlsx")
        else:
            st.info("No circulars found in this category.")

    # 2. Bank Products
    with tabs[1]:
        st.subheader("Bank Products & Schemes")
        st.info("Quick reference for interest rates, eligibility, and features of bank products.")
        
        products = hub_service.list_products()
        if products:
            cols = st.columns(3)
            for i, product in enumerate(products):
                with cols[i % 3]:
                    st.markdown(f"""
                        <div class="glass-card" style="margin-bottom: 1rem;">
                            <div style="font-weight: 800; font-size: 1.1rem; color: #3b82f6;">{product['name']}</div>
                            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">{product['category']}</div>
                            <div style="font-size: 0.9rem; margin-top: 8px;">{product['interest']}</div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No product information available.")
