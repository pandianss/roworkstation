from __future__ import annotations
import streamlit as st
import pandas as pd
import datetime
import html
from src.interface.streamlit.state.services import get_mis_service, get_master_service
from src.interface.streamlit.components.primitives import render_premium_metrics, render_chart_container

def clean_html(s: str) -> str:
    """Helper to remove leading spaces from triple-quoted HTML templates,
    preventing Streamlit from treating them as preformatted code blocks."""
    import re
    return re.sub(r'^\s+', '', s, flags=re.MULTILINE).replace('\n', '')

def render() -> None:
    import base64
    import os
    logo_html = ""
    logo_path = "src/assets/2026logo_min.svg"
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            logo_html = f'<img src="data:image/svg+xml;base64,{encoded}" style="height: 50px; margin-bottom: 20px; display: block;" />'
        except Exception:
            pass

    # 1. Premium Public Header
    c_hero, c_login = st.columns([2.5, 1])
    with c_hero:
        st.markdown(f"""
            <section class="app-hero" style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 60px 40px; color: white; border-radius: 24px; margin-bottom: 40px; height: 100%;">
                {logo_html}
                <div class="app-hero__eyebrow" style="color: rgba(255,255,255,0.8); text-transform: uppercase; letter-spacing: 2px;">Dindigul Regional Office</div>
                <h1 style="font-size: 3rem; font-weight: 800; margin-bottom: 16px;">Regional Business Portal</h1>
                <p style="font-size: 1.2rem; opacity: 0.9; max-width: 600px;">
                    Transparency and Excellence in Banking. Overview of our regional performance, district coverage, and organizational growth.
                </p>
            </section>
        """, unsafe_allow_html=True)
    with c_login:
        with st.container(border=True):
            st.markdown("### 🔒 Staff Login")
            st.caption("Secure workstation access")
            with st.form("staff_login_form"):
                emp_id = st.text_input("Employee ID / Roll Number", placeholder="e.g. 12345")
                if st.form_submit_button("Authenticate", use_container_width=True, type="primary"):
                    if emp_id.strip():
                        st.session_state["manual_login_user"] = emp_id.strip()
                        # Force user state reload
                        if "role" in st.session_state: del st.session_state["role"]
                        if "user_details" in st.session_state: del st.session_state["user_details"]
                        st.rerun()

    mis_service = get_mis_service()
    master_service = get_master_service()
    
    data = mis_service.get_data()
    units_df = master_service.get_units_frame()
    depts_df = master_service.get_departments_frame()
    
    guest_tabs = st.tabs(["📊 Business Overview", "📈 Performance Insights", "👥 Organization"])
    
    with guest_tabs[0]:
        if not data.empty:
            latest_date = data["DATE"].max()
            latest_data = data[data["DATE"] == latest_date]
            
            # 2. Key Regional Metrics
            st.markdown("### 📊 Regional Business Snapshot")
            from src.core.utils.number_utils import format_indian_number
            render_premium_metrics({
                "Total Deposits": f"₹ {format_indian_number(latest_data['TOTAL DEPOSITS'].sum())} Cr",
                "Total Advances": f"₹ {format_indian_number(latest_data['ADV'].sum())} Cr",
                "CD Ratio": f"{latest_data['CD RATIO'].mean():.2f}%",
                "Low Cost (CASA)": f"₹ {format_indian_number(latest_data['CASA'].sum())} Cr",
            })

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Add Infographics for Deposits and Advances Breakup
            st.markdown("### 🥧 Portfolio Composition")
            comp_col1, comp_col2 = st.columns(2)
            
            with comp_col1:
                casa_val = latest_data['CASA'].sum()
                td_val = latest_data['TD'].sum()
                dep_pie_df = pd.DataFrame({"Category": ["CASA", "Term Deposits"], "Amount": [casa_val, td_val]})
                render_chart_container(dep_pie_df, "Category", "Amount", "Deposit Mix", kind="pie")
                
            with comp_col2:
                retail = latest_data.get('TOTAL RETAIL', pd.Series(dtype=float)).sum()
                agri = latest_data.get('CORE AGRI', pd.Series(dtype=float)).sum()
                msme = latest_data.get('MSME', pd.Series(dtype=float)).sum()
                other_adv = max(0, latest_data['ADV'].sum() - (retail + agri + msme))
                adv_pie_df = pd.DataFrame({"Sector": ["Retail", "Agriculture", "MSME", "Others"], "Amount": [retail, agri, msme, other_adv]})
                render_chart_container(adv_pie_df, "Sector", "Amount", "Advances Sectoral Mix (RAM)", kind="pie")

        # 4. District Coverage & Network
        st.divider()
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📍 Regional Network")
            st.markdown("""
                Our region covers **Dindigul** and surrounding areas with a robust network of branches.
                We are committed to financial inclusion across all tiers.
            """)
            
            # Fetch active branch counts per district dynamically
            if not units_df.empty:
                # Exclude Regional Office from active branch count stats
                active_units = units_df[(units_df["Active"] == True) & (units_df["Type"] != "REGIONAL OFFICE")].copy()
                active_units["District"] = active_units["District"].astype(str).str.title().str.strip()
                district_counts = active_units.groupby("District")["Code"].count().to_dict()
            else:
                district_counts = {}

            if district_counts:
                cols = st.columns(len(district_counts))
                for i, (dist, count) in enumerate(sorted(district_counts.items())):
                    cols[i].markdown(f"**{dist}**\n\n{count} Branches")
            else:
                st.info("No active units registered in the directory.")

        with col2:
            st.markdown("### 🏛️ Organization")
            
            # Fetch leadership and department details dynamically
            rm_details = master_service.get_branch_manager("3933")
            rm_name = rm_details.get("name", "The Regional Manager")
            rm_desig = rm_details.get("designation", "Regional Manager")
            
            active_depts = depts_df[depts_df["Active"] == True] if not depts_df.empty else []
            dept_count = len(active_depts)
            
            rm_name_esc = html.escape(str(rm_name))
            rm_desig_esc = html.escape(str(rm_desig))
            
            st.markdown(f"""
                <div class="glass-panel" style="padding: 20px; border-left: 4px solid #10b981;">
                    <div style="font-weight: 700; color: #1e3a8a;">{rm_name_esc}</div>
                    <div style="font-size: 0.9rem; opacity: 0.8; color: #1f2937; font-weight: 500;">{rm_desig_esc}</div>
                    <hr style="margin: 10px 0; border: none; border-top: 1px solid rgba(0,0,0,0.1);">
                    <div style="font-weight: 600;">Operational Hub</div>
                    <div style="font-size: 0.8rem; opacity: 0.9; color: #374151;">{dept_count} Active Specialized Departments</div>
                </div>
            """, unsafe_allow_html=True)

        # 4.5 Branch Demographics & Business Demarcation Infographics
        if not units_df.empty:
            # Exclude Regional Office from active branch count stats
            active_branches = units_df[(units_df["Active"] == True) & (units_df["Type"] != "REGIONAL OFFICE")].copy()
            
            # 1. Population Demographics
            pop_groups = active_branches["Population Group"].astype(str).str.strip().str.upper().tolist()
            rural_count = sum(1 for g in pop_groups if g == "RURAL")
            semi_urban_count = sum(1 for g in pop_groups if g == "SEMI URBAN")
            urban_count = sum(1 for g in pop_groups if g == "URBAN")
            total_pop = len(pop_groups) or 1
            rural_pct = round((rural_count / total_pop) * 100)
            semi_urban_pct = round((semi_urban_count / total_pop) * 100)
            urban_pct = round((urban_count / total_pop) * 100)
            
            # 2. Leadership Hierarchy (Branch Head Grade)
            staff_list = master_service.repo.get_by_category("STAFF")
            staff_grades = {s.code: (s.metadata or {}).get("grade", "Officer") for s in staff_list}
            
            active_sols = [str(c) for c in active_branches["Code"]]
            active_units_list = [u for u in master_service.repo.get_by_category("UNIT") if u.code in active_sols]
            
            branch_head_grades = []
            for u in active_branches.to_dict(orient="records"):
                u_code = str(u["Code"])
                u_record = next((ur for ur in active_units_list if ur.code == u_code), None)
                if u_record:
                    h_id = (u_record.metadata or {}).get("headUserId")
                    grade = staff_grades.get(str(h_id), "MM II") if h_id else "MM II"
                else:
                    grade = "MM II"
                branch_head_grades.append(str(grade).upper().strip())
                
            scale_4_count = sum(1 for g in branch_head_grades if "SM IV" in g or "SCALE IV" in g)
            scale_3_count = sum(1 for g in branch_head_grades if "MM III" in g or "SCALE III" in g)
            scale_2_1_count = len(branch_head_grades) - scale_4_count - scale_3_count
            total_lead = len(branch_head_grades) or 1
            scale_4_pct = round((scale_4_count / total_lead) * 100)
            scale_3_pct = round((scale_3_count / total_lead) * 100)
            scale_2_1_pct = round((scale_2_1_count / total_lead) * 100)
            
            # 3. Business Size Distribution (Interval Based)
            import sqlite3
            from src.infrastructure.persistence.database import DB_PATH
            try:
                conn = sqlite3.connect(DB_PATH)
                mis_df = pd.read_sql("select * from mis_records", conn)
                conn.close()
            except:
                mis_df = pd.DataFrame()
                
            if not mis_df.empty:
                mis_df = mis_df[mis_df["sol"] != 3933]
                mis_df["biz_cr"] = (mis_df["sb"] + mis_df["cd"] + mis_df["td"] + mis_df["adv"]) / 100.0
                mis_df["adv_cr"] = mis_df["adv"] / 100.0
                latest_biz = mis_df.sort_values("date").groupby("sol")[["biz_cr", "adv_cr"]].last().to_dict(orient="index")
            else:
                latest_biz = {}
                
            # Classify each branch using the exact criteria provided:
            # Small: Business <= 10 Crores
            # Medium: Business <= 60 Crores
            # Large: Business <= 125 Crores & Adv >= 30 Crores
            # Very Large: Business <= 500 Crores & Adv >= 100 Crores
            # Extra Large: Business > 500 Crores & Adv >= 300 Crores
            small_count = 0
            medium_count = 0
            large_count = 0
            very_large_count = 0
            extra_large_count = 0
            
            for sol in active_branches["Code"]:
                sol_int = int(sol)
                if sol_int in latest_biz:
                    biz_cr = latest_biz[sol_int]["biz_cr"]
                    adv_cr = latest_biz[sol_int]["adv_cr"]
                else:
                    biz_cr, adv_cr = 110.0, 65.0  # Fallback to defaults
                
                if biz_cr <= 10.0:
                    small_count += 1
                elif biz_cr <= 60.0:
                    medium_count += 1
                elif biz_cr <= 125.0:
                    if adv_cr >= 30.0:
                        large_count += 1
                    else:
                        medium_count += 1
                elif biz_cr <= 500.0:
                    if adv_cr >= 100.0:
                        very_large_count += 1
                    elif adv_cr >= 30.0:
                        large_count += 1
                    else:
                        medium_count += 1
                else:  # biz_cr > 500.0
                    if adv_cr >= 300.0:
                        extra_large_count += 1
                    elif adv_cr >= 100.0:
                        very_large_count += 1
                    elif adv_cr >= 30.0:
                        large_count += 1
                    else:
                        medium_count += 1
            
            total_biz_count = len(active_branches) or 1
            small_pct = round((small_count / total_biz_count) * 100)
            medium_pct = round((medium_count / total_biz_count) * 100)
            large_pct = round((large_count / total_biz_count) * 100)
            very_large_pct = round((very_large_count / total_biz_count) * 100)
            extra_large_pct = round((extra_large_count / total_biz_count) * 100)
            
            st.divider()
            st.markdown("### 📊 Branch Demographics & Business Demarcation")
            st.caption("Detailed classification of our active retail network by population sectors, officer scale hierarchy, and business size tiers.")
            
            demo_cols = st.columns(3)
            
            with demo_cols[0]:
                st.markdown(clean_html(f"""
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 12px; height: 100%;">
                        <div style="font-weight: 800; font-size: 0.95rem; color: #60a5fa; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                            🌾 Population Sectors
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            <div>
                                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                                    <span style="color: #94a3b8;">🏡 Semi-Urban</span>
                                    <span style="font-weight: 700; color: #ffffff;">{semi_urban_count} Branches ({semi_urban_pct}%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden;">
                                    <div style="width: {semi_urban_pct}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #60a5fa); border-radius: 10px;"></div>
                                </div>
                            </div>
                            <div>
                                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                                    <span style="color: #94a3b8;">🌾 Rural</span>
                                    <span style="font-weight: 700; color: #ffffff;">{rural_count} Branches ({rural_pct}%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden;">
                                    <div style="width: {rural_pct}%; height: 100%; background: linear-gradient(90deg, #10b981, #34d399); border-radius: 10px;"></div>
                                </div>
                            </div>
                            <div>
                                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                                    <span style="color: #94a3b8;">🏢 Urban</span>
                                    <span style="font-weight: 700; color: #ffffff;">{urban_count} Branches ({urban_pct}%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden;">
                                    <div style="width: {urban_pct}%; height: 100%; background: linear-gradient(90deg, #f59e0b, #fbbf24); border-radius: 10px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                """), unsafe_allow_html=True)
                
            with demo_cols[1]:
                st.markdown(clean_html(f"""
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 12px; height: 100%;">
                        <div style="font-weight: 800; font-size: 0.95rem; color: #fbbf24; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                            👑 Scale Hierarchy (Branch Head)
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            <div>
                                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                                    <span style="color: #94a3b8;">Scale IV (Chief Manager)</span>
                                    <span style="font-weight: 700; color: #ffffff;">{scale_4_count} ({scale_4_pct}%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden;">
                                    <div style="width: {scale_4_pct}%; height: 100%; background: linear-gradient(90deg, #fbbf24, #f59e0b); border-radius: 10px;"></div>
                                </div>
                            </div>
                            <div>
                                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                                    <span style="color: #94a3b8;">Scale III (Senior Manager)</span>
                                    <span style="font-weight: 700; color: #ffffff;">{scale_3_count} ({scale_3_pct}%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden;">
                                    <div style="width: {scale_3_pct}%; height: 100%; background: linear-gradient(90deg, #60a5fa, #3b82f6); border-radius: 10px;"></div>
                                </div>
                            </div>
                            <div>
                                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                                    <span style="color: #94a3b8;">Scale II / I (Manager/Officer)</span>
                                    <span style="font-weight: 700; color: #ffffff;">{scale_2_1_count} ({scale_2_1_pct}%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden;">
                                    <div style="width: {scale_2_1_pct}%; height: 100%; background: linear-gradient(90deg, #a78bfa, #8b5cf6); border-radius: 10px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                """), unsafe_allow_html=True)
                
            with demo_cols[2]:
                st.markdown(clean_html(f"""
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 12px; height: 100%;">
                        <div style="font-weight: 800; font-size: 0.95rem; color: #a78bfa; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                            💼 Business Size Tiers
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 10px;">
                            <!-- Multi-segment Stacked Bar Infographic -->
                            <div style="width: 100%; height: 14px; background: rgba(255,255,255,0.05); border-radius: 100px; display: flex; overflow: hidden; margin-bottom: 4px; border: 1px solid rgba(255,255,255,0.05);">
                                <div style="width: {small_pct}%; height: 100%; background: #ef4444;" title="Small (≤10Cr): {small_count}"></div>
                                <div style="width: {medium_pct}%; height: 100%; background: #f59e0b;" title="Medium (≤60Cr): {medium_count}"></div>
                                <div style="width: {large_pct}%; height: 100%; background: #3b82f6;" title="Large (≤125Cr & Adv≥30Cr): {large_count}"></div>
                                <div style="width: {very_large_pct}%; height: 100%; background: #8b5cf6;" title="Very Large (≤500Cr & Adv≥100Cr): {very_large_count}"></div>
                                <div style="width: {extra_large_pct}%; height: 100%; background: #10b981;" title="Extra Large (&gt;500Cr & Adv≥300Cr): {extra_large_count}"></div>
                            </div>
                            <!-- Legend Grid -->
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.70rem;">
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <span style="display: inline-block; width: 8px; height: 8px; background: #ef4444; border-radius: 50%;"></span>
                                    <span style="color: #94a3b8;">Small: <strong>{small_count}</strong></span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <span style="display: inline-block; width: 8px; height: 8px; background: #f59e0b; border-radius: 50%;"></span>
                                    <span style="color: #94a3b8;">Medium: <strong>{medium_count}</strong></span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <span style="display: inline-block; width: 8px; height: 8px; background: #3b82f6; border-radius: 50%;"></span>
                                    <span style="color: #94a3b8;">Large: <strong>{large_count}</strong></span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <span style="display: inline-block; width: 8px; height: 8px; background: #8b5cf6; border-radius: 50%;"></span>
                                    <span style="color: #94a3b8;">Very Large: <strong>{very_large_count}</strong></span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 4px; grid-column: span 2;">
                                    <span style="display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%;"></span>
                                    <span style="color: #94a3b8;">Extra Large: <strong>{extra_large_count}</strong></span>
                                </div>
                            </div>
                        </div>
                    </div>
                """), unsafe_allow_html=True)

        # 5. Public Interactive Branch Finder
        st.divider()
        st.markdown("### 🔍 Regional Branch Directory")
        st.caption("Instantly find location details, opening dates, and designated unit authorities.")
        
        search_query = st.text_input("Search by Branch Name, SOL Code, or District", placeholder="e.g. Dindigul, 3933, Palani", key="guest_search_query")
        
        if search_query:
            query = search_query.lower().strip()
            if not units_df.empty:
                match_df = units_df[
                    units_df["Code"].astype(str).str.lower().str.contains(query) |
                    units_df["Name"].str.lower().str.contains(query) |
                    units_df["District"].astype(str).str.lower().str.contains(query)
                ]
            else:
                match_df = pd.DataFrame()
            
            if not match_df.empty:
                for _, row in match_df.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([1.2, 2, 1.8])
                        with c1:
                            st.markdown(f"##### 🏦 SOL {row['Code']}")
                            status_label = "🟢 Active" if row["Active"] else "🔴 Closed"
                            st.caption(f"Status: {status_label}")
                        with c2:
                            st.markdown(f"**{row['Name']}**")
                            st.caption(f"📍 District: {row['District']} | Group: {row['Population Group']}")
                            if pd.notna(row["Open Date"]):
                                try:
                                    open_date_str = row["Open Date"].strftime("%d-%b-%Y")
                                except:
                                    open_date_str = str(row["Open Date"])
                                st.caption(f"🗓️ Open Date: {open_date_str}")
                        with c3:
                            st.markdown(f"👤 **Head:** {row['Head']}")
                            st.markdown(f"👥 **2nd Line:** {row['2nd Line']}")
            else:
                st.warning("No branches match your search query.")
        else:
            st.info("Use the search bar above to look up branch profiles within our regional network.")

        # 6. Recent Public Announcements & Notices
        st.divider()
        st.markdown("### 📢 Announcements & Notices")
        
        from src.application.services.circular_service import CircularService
        try:
            circ_service = CircularService()
            all_circulars = circ_service.get_all()
        except Exception:
            all_circulars = []
            
        if all_circulars:
            # Sort circulars by date (newest first)
            try:
                sorted_circs = sorted(all_circulars, key=lambda x: pd.to_datetime(x.get("date"), errors="coerce"), reverse=True)[:3]
            except Exception:
                sorted_circs = all_circulars[:3]
                
            circ_cols = st.columns(3)
            for i, circ in enumerate(sorted_circs):
                with circ_cols[i]:
                    with st.container(border=True):
                        st.markdown(f"📄 **{circ.get('number', 'RO Notice')}**")
                        st.caption(f"Issued: {circ.get('date', 'N/A')} | Category: {circ.get('category', 'General')}")
                        st.markdown(f"**{circ.get('title', '')}**")
        else:
            st.info("No recent regional announcements have been published.")

        # 7. Recent Achievements (Premium Layout)
        st.divider()
        st.markdown("### 🏆 Regional Achievements")
        
        from src.interface.streamlit.state.services import get_achievement_service
        try:
            ach_service = get_achievement_service()
            achievements = ach_service.get_all()
        except Exception:
            achievements = []
            
        if achievements:
            for r in range(0, len(achievements), 3):
                row_achs = achievements[r:r+3]
                cols = st.columns(len(row_achs))
                for i, ach in enumerate(row_achs):
                    title_esc = html.escape(str(ach['title']))
                    desc_esc = html.escape(str(ach['desc']))
                    cols[i].markdown(f"""
                        <div class="glass-panel" style="padding: 15px; height: 100%; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; background: rgba(255,255,255,0.02);">
                            <div style="font-size: 1.5rem; margin-bottom: 10px;">🌟</div>
                            <div style="font-weight: 700; color: #1e3a8a; margin-bottom: 6px;">{title_esc}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8; color: #374151; font-weight: 500;">{desc_esc}</div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No corporate achievements published at the moment.")
            
    with guest_tabs[1]:
        if not data.empty:
            st.markdown("### 📈 Performance Insights")
            pi_col1, pi_col2 = st.columns([1, 1])
            with pi_col1:
                cd_ratio = latest_data['CD RATIO'].mean()
                import plotly.graph_objects as go
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = cd_ratio,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "CD Ratio (%)", 'font': {'size': 18}},
                    gauge = {
                        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': "#10b981" if cd_ratio >= 60 else "#f59e0b"},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 40], 'color': "rgba(239, 68, 68, 0.3)"},
                            {'range': [40, 60], 'color': "rgba(245, 158, 11, 0.3)"},
                            {'range': [60, 100], 'color': "rgba(16, 185, 129, 0.3)"}],
                    }
                ))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#f8fafc"}, margin=dict(t=50, b=10, l=20, r=20), height=300)
                st.plotly_chart(fig, use_container_width=True)

            with pi_col2:
                q1 = latest_data['REC Q1'].sum()
                q2 = latest_data['REC Q2'].sum()
                q3 = latest_data['REC Q3'].sum()
                q4 = latest_data['REC Q4'].sum()
                rec_df = pd.DataFrame({"Quarter": ["Q1", "Q2", "Q3", "Q4"], "Recovery (Cr)": [q1, q2, q3, q4]})
                render_chart_container(rec_df, "Quarter", "Recovery (Cr)", "Quarterly Recovery Progress", kind="bar")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📊 Performance Trajectory")
            from src.core.utils.financial_year import get_fy_start
            fy_start = pd.to_datetime(get_fy_start(datetime.date.today()))
            hist = data[data["DATE"] >= fy_start].groupby("DATE")[["TOTAL DEPOSITS", "ADV"]].sum().reset_index()
            render_chart_container(hist, "DATE", ["TOTAL DEPOSITS", "ADV"], "Regional Business Growth (Current FY)")
        else:
            st.info("Performance data is currently unavailable.")

    with guest_tabs[2]:
        from src.interface.streamlit.components.org_chart import render_org_chart
        render_org_chart(master_service)
