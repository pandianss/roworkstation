from __future__ import annotations
import streamlit as st
import pandas as pd
import datetime
from src.interface.streamlit.state.services import (
    get_mis_service, get_circular_service, get_doc_service_v4, get_master_service
)
from src.application.services.communication_service import CommunicationService
from src.infrastructure.persistence.database import get_db_session
from src.interface.streamlit.components.primitives import render_action_bar, render_premium_metrics, render_data_table, render_chart_container
from src.core.utils.number_utils import format_crore
from src.core.utils.financial_year import get_fy_start

def render() -> None:
    # 1. Branch Identity
    sol_id = st.session_state.get("sol", "3933") # Default for demo
    branch_name = st.session_state.get("branch_name", "Dindigul Main")
    
    render_action_bar(f"Branch Dashboard: {branch_name}", ["Branch: "+str(sol_id), "Real-time", "Connected"])

    # Campaign running strip ticker
    from src.application.services.campaign_service import CampaignService
    try:
        campaign_service = CampaignService()
        active_campaigns = [c for c in campaign_service.get_all() if c.get("status") == "Active"]
    except Exception:
        active_campaigns = []

    if active_campaigns:
        ticker_items = []
        for c in active_campaigns:
            metric = c.get("target_metric", "Business")
            val = c.get("target_value", 0)
            from src.core.utils.number_utils import format_campaign_target
            val_str = format_campaign_target(val, metric)
            ticker_items.append(
                f"🚀 <strong>CAMPAIGN ACTIVE:</strong> <span style='color:#fbbf24;'>{c.get('name')}</span> "
                f"({metric} Target: {val_str}) "
                f"| Valid: {c.get('start_date')} to {c.get('end_date')}"
            )
        ticker_content = " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(ticker_items)
    else:
        ticker_content = "📢 <strong>RO COCKPIT:</strong> Drive CASA & Retail Advances | Enforce Trilingual Compliance across all units | Customer-First Excellence"

    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 10px; border-radius: 8px; font-weight: bold; margin-bottom: 20px; overflow: hidden; white-space: nowrap; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <marquee scrollamount="6" behavior="scroll" direction="left" onmouseover="this.stop();" onmouseout="this.start();" style="cursor: pointer;">
                {ticker_content}
            </marquee>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["🏠 Overview", "👥 Org Chart", "📢 Circulars", "🚀 Campaigns", "🏗️ Wizards", "💬 RO Coordination", "🛍️ Products"])

    master_service = get_master_service()

    # --- TAB: OVERVIEW ---
    with tabs[0]:
        mis_service = get_mis_service()
        data = mis_service.get_data()
        
        if not data.empty:
            # Filter for this branch
            br_data = data[data["SOL"] == int(sol_id)]
            if not br_data.empty:
                latest = br_data.sort_values("DATE").iloc[-1]
                st.markdown(f"#### 📊 {branch_name} Performance")
                render_premium_metrics({
                    "Total Deposits": format_crore(latest['TOTAL DEPOSITS']),
                    "Total Advances": format_crore(latest['TOTAL ADVANCES']),
                    "CASA Ratio": f"{(latest['CASA']/latest['TOTAL DEPOSITS']*100):.2f}%" if latest['TOTAL DEPOSITS'] > 0 else "0%",
                    "NPA %": f"{latest['NPA %']}%",
                })
                
                st.markdown("<br>", unsafe_allow_html=True)
                # Comparison with Region
                reg_avg = data[data["DATE"] == latest["DATE"]]["TOTAL DEPOSITS"].mean()
                st.caption(f"Branch Deposit: {format_crore(latest['TOTAL DEPOSITS'])} vs Regional Avg: {format_crore(reg_avg)}")

                # Trend Chart (Current FY)
                st.markdown("#### 📈 Branch Business Trend")
                fy_start = pd.to_datetime(get_fy_start(datetime.date.today()))
                br_hist = br_data[br_data["DATE"] >= fy_start].groupby("DATE")[["TOTAL DEPOSITS", "ADV"]].sum().reset_index()
                render_chart_container(br_hist, "DATE", ["TOTAL DEPOSITS", "ADV"], f"{branch_name} Growth (Current FY)")
            else:
                st.warning(f"No MIS data found for SOL {sol_id}.")

    # --- TAB: ORG CHART ---
    with tabs[1]:
        from src.interface.streamlit.components.org_chart import render_org_chart
        render_org_chart(master_service)

    # --- TAB: CIRCULARS ---
    with tabs[2]:
        circ_service = get_circular_service()
        doc_service = get_doc_service_v4()
        all_circs = circ_service.get_all()
        
        st.markdown("### 📢 Regional Notifications")
        if not all_circs:
            st.info("No active circulars found.")
        else:
            for i, c in enumerate(all_circs):
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"**{c.get('subject', 'Circular')}**")
                    c1.caption(f"Ref: {c.get('ref_no')} | Date: {c.get('date')}")
                    if c2.button("Prepare PDF", key=f"br_prep_{i}"):
                        st.session_state[f"br_pdf_{i}"] = doc_service.generate_circular_pdf(c)
                    if f"br_pdf_{i}" in st.session_state:
                        c2.download_button("📥 Download", data=st.session_state[f"br_pdf_{i}"], file_name=f"Circular_{i}.pdf", key=f"br_dl_{i}")

    # --- TAB: CAMPAIGNS ---
    with tabs[3]:
        from src.application.services.campaign_service import CampaignService
        camp_service = CampaignService()
        campaigns = camp_service.get_all()
        
        st.markdown("### 🚀 Ongoing Regional Campaigns")
        active = [c for c in campaigns if c["status"] == "Active"]
        if not active:
            st.info("No active campaigns.")
        else:
            for c in active:
                with st.container(border=True):
                    st.markdown(f"#### {c['name']}")
                    st.caption(f"Valid: {c['start_date']} to {c['end_date']}")
                    
                    # Progress Simulation
                    progress = 0.65 # Dummy progress for demo
                    st.progress(progress, text=f"Branch Progress: {progress*100:.0f}% of ₹{c['target_value']} Cr")
                    st.markdown(f"**Focus Area:** {c['target_metric']}")
        
        st.divider()
        st.markdown("### 📁 Recently Completed")
        completed = [c for c in campaigns if c["status"] == "Completed"]
        if completed:
            for c in completed[:2]:
                st.caption(f"✅ {c['name']} - Target: {c['target_value']} Cr (Finished: {c['end_date']})")

    # --- TAB: WIZARDS ---
    with tabs[4]:
        st.markdown("### 🛠️ Approved Branch Wizards")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div class="glass-panel" style="padding: 20px;">
                    <h4>✉️ High Value DD</h4>
                    <p style="font-size: 0.85rem;">Required for reporting DDs above ₹ 5 Lakhs.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Open DD Wizard", use_container_width=True):
                st.session_state["branch_wiz"] = "high_value_dd"
                st.rerun()

        with col2:
            st.markdown("""
                <div class="glass-panel" style="padding: 20px;">
                    <h4>📄 Office Note Generator</h4>
                    <p style="font-size: 0.85rem;">Standard template for internal approvals.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Open Office Note Wizard", use_container_width=True):
                st.session_state["branch_wiz"] = "office_note"
                st.rerun()
        
        # Sub-render wizards if selected
        if st.session_state.get("branch_wiz") == "high_value_dd":
            st.divider()
            from src.interface.streamlit.pages.operational_wizards import render_high_value_dd_wizard
            render_high_value_dd_wizard()
        elif st.session_state.get("branch_wiz") == "office_note":
            st.divider()
            from src.interface.streamlit.pages.execution import render_office_note_tab
            render_office_note_tab(doc_service, get_master_service)

    # --- TAB: COMS (RO COORDINATION) ---
    with tabs[5]:
        st.markdown("### 💬 Regional Office Coordination")
        st.caption("Communicate requests directly to Regional Office departments.")
        
        if "coms_success_msg" in st.session_state:
            st.success(st.session_state.pop("coms_success_msg"))
        
        with get_db_session() as session:
            com_svc = CommunicationService(session)
            
            with st.expander("➕ Raise New Request / Inquiry"):
                with st.form("br_com_form"):
                    depts_df = master_service.get_departments_frame()
                    if not depts_df.empty:
                        dept_list = depts_df[depts_df["Active"] == True]["Name (En)"].tolist()
                        if not dept_list:
                            dept_list = ["IT", "OPERATIONS", "PLANNING", "ADVANCES", "HRM", "GENERAL ADMIN"]
                    else:
                        dept_list = ["IT", "OPERATIONS", "PLANNING", "ADVANCES", "HRM", "GENERAL ADMIN"]
                    
                    target_dept = st.selectbox("Select RO Department", dept_list)
                    subj = st.text_input("Subject")
                    msg = st.text_area("Detailed Message")
                    priority = st.select_slider("Priority", ["LOW", "NORMAL", "HIGH", "URGENT"], value="NORMAL")
                    
                    if st.form_submit_button("Submit to RO"):
                        com_svc.create_request(
                            sender_unit=str(sol_id),
                            sender_name=st.session_state.get("username", "Branch Manager"),
                            receiver_dept=target_dept,
                            subject=subj,
                            message=msg,
                            priority=priority
                        )
                        st.session_state["coms_success_msg"] = f"✅ Request sent to RO {target_dept} successfully!"
                        st.rerun()

            # 2. View History
            st.markdown("#### 📜 Request History")
            requests = com_svc.get_requests_from_unit(str(sol_id))
            if not requests:
                st.info("No previous requests found.")
            else:
                for r in requests:
                    status_color = {"PENDING": "gray", "IN_PROGRESS": "blue", "RESOLVED": "green", "CLOSED": "red"}.get(r.status, "black")
                    with st.container(border=True):
                        c1, c2 = st.columns([4, 1])
                        c1.markdown(f"**{r.subject}** (To: {r.receiver_dept})")
                        c1.caption(f"Status: :{status_color}[{r.status}] | Sent: {r.created_at.strftime('%d.%m.%Y')}")
                        c1.write(f"_{r.message}_")
                        
                        if r.response_message:
                            st.markdown(f"""
                                <div style="background: #f0fdf4; padding: 10px; border-radius: 8px; border: 1px solid #bbf7d0; margin-top: 10px;">
                                    <strong>RO Response:</strong> {r.response_message}
                                    <div style="font-size: 0.75rem; color: #166534; margin-top: 5px;">
                                        By {r.responded_by} on {r.responded_at.strftime('%d.%m.%Y %H:%M')}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

    # --- TAB: PRODUCTS ---
    with tabs[6]:
        st.markdown("### 🛍️ Product Catalog")
        products = [
            {"name": "Home Loan Plus", "cat": "Retail", "desc": "Reduced ROI for Senior Citizens.", "icon": "🏠"},
            {"name": "MSME Vidyut", "cat": "MSME", "desc": "Fast track credit for green energy units.", "icon": "⚡"},
            {"name": "Gold Overdraft", "cat": "Agri", "desc": "Instant liquidity against gold ornaments.", "icon": "👑"},
        ]
        
        for p in products:
            with st.container(border=True):
                c1, c2 = st.columns([1, 4])
                c1.markdown(f"<div style='font-size: 3rem;'>{p['icon']}</div>", unsafe_allow_html=True)
                c2.markdown(f"**{p['name']}** ({p['cat']})")
                c2.write(p['desc'])
                c2.button("Download Brochure", key=f"brochure_{p['name']}")
