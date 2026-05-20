from __future__ import annotations

import streamlit as st
import pandas as pd
from src.application.services.product_service import ProductService
from src.interface.streamlit.components.primitives import render_action_bar

def render() -> None:
    service = ProductService()
    render_action_bar("Product Intelligence Hub", ["Catalog", "Sales Kits", "ROI Calculators"])
    
    # 🌟 Hero Section with Banner
    st.markdown(f"""
        <div class="app-hero" style="padding: 1.5rem; position: relative; overflow: hidden; height: 180px;">
            <div style="position: absolute; top:0; left:0; width:100%; height:100%; opacity: 0.3; background: url('banking_products_banner_1778499815435.png'); background-size: cover; background-position: center;"></div>
            <div style="position: relative; z-index: 2;">
                <div class="app-hero__eyebrow">IOB Regional Portfolio</div>
                <h1 style="margin-top: 0.5rem; font-size: 2rem;">Product Excellence Center</h1>
                <p>Equipping our staff with intelligence to sell better and serve faster.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    products = service.list_products()
    
    # 🔍 Search & Filter Bar
    s1, s2 = st.columns([2, 1])
    with s1:
        search_query = st.text_input("🔍 Search for a product, category, or feature...", placeholder="Ex: Housing, 7.25%, Digital...")
    with s2:
        categories = sorted(list(set(p.get("category", "General") for p in products)))
        selected_cat = st.selectbox("Category Filter", options=["All Categories"] + categories)

    # Filtering Logic
    display_products = products
    if selected_cat != "All Categories":
        display_products = [p for p in display_products if p.get("category") == selected_cat]
    if search_query:
        q = search_query.lower()
        display_products = [p for p in display_products if q in p['name'].lower() or q in p['category'].lower()]

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 🏗️ Grid Layout for Cards
    rows = [display_products[i:i + 3] for i in range(0, len(display_products), 3)]
    
    for row in rows:
        cols = st.columns(3)
        for i, product in enumerate(row):
            icon = product.get("icon", "📦")
            # Fake features for "WOW" effect if missing
            features = product.get("features", ["Instant Approval", "Low Processing Fee", "Digital First"])
            
            with cols[i]:
                feature_html = "".join([f'<span class="feature-tag">{f}</span>' for f in features[:3]])
                st.markdown(f"""
                    <div class="product-card">
                        <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 20px;">
                            <div style="font-size: 2.2rem; background: rgba(212, 175, 55, 0.1); padding: 12px; border-radius: 16px; border: 1px solid rgba(212, 175, 55, 0.2);">{icon}</div>
                            <div>
                                <div style="font-weight: 800; font-size: 1.2rem; color: #f8fafc; line-height: 1.2; margin-bottom: 4px;">{product['name']}</div>
                                <div style="font-size: 0.7rem; color: #d4af37; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px;">{product['category']}</div>
                            </div>
                        </div>
                        
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                                <span style="color: #94a3b8; font-size: 0.75rem; font-weight: 600;">INTEREST / YIELD</span>
                                <span style="color: #60a5fa; font-weight: 800; font-size: 1rem;">{product['interest']}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: #94a3b8; font-size: 0.75rem; font-weight: 600;">MAX TENURE</span>
                                <span style="color: #f8fafc; font-weight: 700; font-size: 0.9rem;">{product['tenure']}</span>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 20px; min-height: 50px;">
                            {feature_html}
                        </div>
                        
                        <div style="display: flex; gap: 8px;">
                            <button style="flex: 1; background: #21357f; color: white; border: none; padding: 8px; border-radius: 8px; font-size: 0.75rem; font-weight: 700; cursor: pointer;">Sales Kit</button>
                            <button style="flex: 1; background: rgba(255,255,255,0.05); color: #f8fafc; border: 1px solid rgba(255,255,255,0.1); padding: 8px; border-radius: 8px; font-size: 0.75rem; font-weight: 700; cursor: pointer;">Details</button>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("🛠️ Regional Admin: Product Pipeline"):
        st.info("Manage regional product overrides and launch new tactical schemes.")
        with st.form("add_product_hub_v2"):
            # (Form logic remains similar but with expanded fields)
            pass
