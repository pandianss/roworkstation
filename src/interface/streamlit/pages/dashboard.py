from __future__ import annotations

import pandas as pd
import streamlit as st
import datetime
import html
import plotly.express as px
import streamlit.components.v1 as components

from src.application.services.guardian_service import GuardianService
from src.application.services.task_service import TaskService
from src.application.services.circular_service import CircularService
from src.application.services.document import DocumentService
from src.application.services.returns_service import ReturnsService
from src.application.use_cases.mis.service import MISAnalyticsService
from src.interface.streamlit.components.primitives import (
    render_action_bar, render_data_table, render_premium_metrics, 
    render_section_divider, render_info_banner
)
from src.interface.streamlit.state.services import (
    get_task_service, get_guardian_service, get_returns_service, 
    get_search_service, get_circular_service, get_doc_service_v4
)

@st.dialog("📄 Document Preview", width="large")
def show_preview(circular_data: dict, index: int) -> None:
    st.markdown(f"#### {circular_data.get('subject')}")
    st.caption(f"Ref: {circular_data.get('ref_no')} | Date: {circular_data.get('date')}")
    
    html = get_doc_service_v4().generate_circular_html(circular_data)
    components.html(html, height=500, scrolling=True)
    
    pdf_key = f"circ_pdf_cache_{index}"
    if pdf_key not in st.session_state:
        if st.button("🖨️ Prepare PDF Download", use_container_width=True):
            with st.spinner("Generating High-Quality PDF..."):
                st.session_state[pdf_key] = get_doc_service_v4().generate_circular_pdf(circular_data)
            st.rerun()
    else:
        st.download_button("📥 Save PDF Now", data=st.session_state[pdf_key], file_name=f"Circular_{index}.pdf", use_container_width=True, type="primary")

def render() -> None:
    username = st.session_state.get("username", "")
    task_service = get_task_service()
    guardian_service = get_guardian_service()
    returns_service = get_returns_service()
    mis_service = MISAnalyticsService()
    
    # 1. DATA AGGREGATION
    tasks_summary = task_service.get_task_summary(username)
    mis_df = mis_service.get_data()
    # Use dict for caching compatibility in build_snapshot
    snapshot = mis_service.build_snapshot({"selected_date": None, "sols": None}) if not mis_df.empty else None
    
    # Header Section
    st.markdown('<h1 class="text-gold" style="margin-bottom:0.2rem; font-size: 2.8rem; letter-spacing: -0.03em;">Regional Command Center</h1>', unsafe_allow_html=True)
    render_action_bar("Strategic Oversight & Intelligence", ["V3.0 Stable", "Live Analytics", "Guardian Active"])

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
            c_name = html.escape(str(c.get('name', '')))
            ticker_items.append(
                f"🚀 <strong>CAMPAIGN ACTIVE:</strong> <span style='color:#fbbf24;'>{c_name}</span> "
                f"({html.escape(metric)} Target: {html.escape(val_str)}) "
                f"| Valid: {html.escape(str(c.get('start_date', '')))} to {html.escape(str(c.get('end_date', '')))}"
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

    # 2. EXECUTIVE PULSE (KPIs)
    if snapshot:
        kpis = snapshot.kpis
        from src.core.utils.number_utils import format_crore
        render_premium_metrics({
            "Advances": format_crore(kpis['Total Advances']),
            "Deposits": format_crore(kpis['Total Deposits']),
            "CD Ratio": f"{kpis['CD Ratio']:.1f}%",
            "NPA": f"{kpis.get('NPA %', 0.0):.2f}%",
            "Open Tasks": tasks_summary["open"],
            "Alerts": len(guardian_service.list_followups())
        })
    else:
        render_premium_metrics({
            "Open Tasks": tasks_summary["open"],
            "Overdue": tasks_summary["overdue"],
            "Pending Returns": len([r for r in returns_service.get_all() if r["status"] == "Pending"]),
            "Guardian Alerts": len(guardian_service.list_followups()),
        })

    render_section_divider()

    # 3. MAIN DASHBOARD LAYOUT
    col_main, col_side = st.columns([2.2, 1])

    with col_main:
        # A. Performance Trend (Compact Sparkline)
        if snapshot and not pd.DataFrame(snapshot.history_rows).empty:
            with st.container(border=True):
                st.markdown("#### 📈 Regional Growth Velocity")
                hist = pd.DataFrame(snapshot.history_rows)
                hist["DATE"] = pd.to_datetime(hist["DATE"])
                trend = hist.groupby("DATE", as_index=False)[["ADV", "TOTAL DEPOSITS"]].sum()
                fig = px.line(trend, x="DATE", y=["ADV", "TOTAL DEPOSITS"], 
                            template="plotly_dark", height=180, color_discrete_sequence=["#3b82f6", "#10b981"])
                fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # B. Active Action Queue (Priority Tasks)
        st.markdown('<div class="text-gold" style="font-size: 1.1rem; margin-top: 1rem; margin-bottom: 0.5rem;">⚡ Priority Action Queue</div>', unsafe_allow_html=True)
        task_frame = pd.DataFrame(tasks_summary["tasks"])
        if not task_frame.empty:
            # Show only top priority tasks in dashboard for density
            display_tasks = task_frame.sort_values("priority").head(8)
            render_data_table(display_tasks[["title", "priority", "status", "due_date"]], "Critical Tasks", "dash_tasks.xlsx")
        else:
            st.info("Your action queue is empty. Operational peace achieved.")

        # C. Global Search (Floating style)
        with st.expander("🔍 Deep Registry Search", expanded=False):
            query = st.text_input("Search workstation...", placeholder="Staff, Units, or Circulars...", key="dash_global_search")
            if query:
                search_service = get_search_service()
                results = pd.DataFrame(search_service.search(query, username))
                if not results.empty:
                    render_data_table(results, "Search Matches", "search.xlsx")

        # D. Recent Circulars (Compact List)
        st.markdown('<div class="text-gold" style="font-size: 1.1rem; margin-top: 1.5rem; margin-bottom: 0.5rem;">📢 Latest Circulars</div>', unsafe_allow_html=True)
        circ_service = get_circular_service()
        all_circs = circ_service.get_all()
        if all_circs:
            with st.container(border=True):
                # Hidden marker to precisely target this specific container with CSS
                st.markdown('<div class="circular-list-marker" style="display:none;"></div>', unsafe_allow_html=True)
                st.markdown("""
                    <style>
                    /* 1. Crush the vertical gap between buttons ONLY in this specific container */
                    div[data-testid="stVerticalBlock"]:has(> div.element-container > .circular-list-marker) {
                        gap: 0rem !important;
                    }
                    
                    /* 2. Force buttons to be left-aligned and compact */
                    div[data-testid="stVerticalBlock"]:has(> div.element-container > .circular-list-marker) div[data-testid="stButton"] {
                        display: flex !important;
                        justify-content: flex-start !important;
                        width: 100% !important;
                    }
                    div[data-testid="stVerticalBlock"]:has(> div.element-container > .circular-list-marker) div[data-testid="stButton"] button {
                        padding: 0px 4px !important;
                        min-height: 28px !important;
                        border: none !important;
                        background-color: transparent !important;
                        text-align: left !important;
                    }
                    
                    /* 3. Force text inside the button to be left-aligned */
                    div[data-testid="stVerticalBlock"]:has(> div.element-container > .circular-list-marker) div[data-testid="stButton"] p {
                        text-align: left !important;
                        font-size: 0.9rem !important;
                        margin: 0 !important;
                    }
                    
                    /* 4. Flashing Badge Animation */
                    @keyframes flash-badge {
                        0%, 100% { opacity: 1; transform: scale(1); }
                        50% { opacity: 0.7; transform: scale(1.05); }
                    }
                    
                    /* 5. Target buttons immediately following a new-badge marker */
                    div.element-container:has(> .new-badge-marker) + div.element-container button p::after {
                        content: "NEW";
                        display: inline-block;
                        background-color: #ef4444;
                        color: #ffffff;
                        font-size: 0.65rem;
                        font-weight: bold;
                        padding: 2px 6px;
                        border-radius: 4px;
                        margin-left: 10px;
                        animation: flash-badge 1.5s infinite;
                        vertical-align: middle;
                        box-shadow: 0 0 8px rgba(239,68,68,0.4);
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                for i, c in enumerate(all_circs[:5]):
                    # Check age
                    is_new = False
                    try:
                        c_date_str = str(c.get('date', ''))
                        if c_date_str:
                            c_date = datetime.datetime.strptime(c_date_str, "%Y-%m-%d").date()
                            if (datetime.date.today() - c_date).days <= 3:
                                is_new = True
                    except Exception:
                        pass
                        
                    if is_new:
                        st.markdown('<div class="new-badge-marker" style="display:none; height:0px;"></div>', unsafe_allow_html=True)
                        
                    # Single tight row formatted like a link
                    label = f"📄 [{c.get('dept', 'GEN')}] {c.get('ref_no', 'N/A')} ({c.get('date')})  ➔  {c.get('subject', 'Circular')}"
                    
                    # Dropping use_container_width=True forces it to left align natively
                    if st.button(label, key=f"circ_btn_{i}", type="tertiary"):
                        show_preview(c, i)
                
                st.markdown("<hr style='margin: 4px 0px 8px 0px; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
                if st.button("🗄️ Open Archive Hub", use_container_width=True):
                    st.session_state["requested_page"] = "Central Archive"
                    st.rerun()

    with col_side:
        # 1. Operational Guard (Guardian & Returns)
        st.markdown("#### 🛡️ Operational Guard")
        t_guard1, t_guard2 = st.tabs(["Alerts", "Returns"])
        
        with t_guard1:
            alerts = guardian_service.as_frame()
            if not alerts.empty:
                for _, row in alerts.head(4).iterrows():
                    branch_name = html.escape(str(row.get('BRANCH', 'Alert')))
                    remarks = html.escape(str(row.get('REMARKS', ''))[:45])
                    st.markdown(f"""
                        <div class="glass-panel" style="margin-bottom: 6px; padding: 10px; border-left: 3px solid #ef4444; background: #1e293b55;">
                            <div style="font-weight: 600; font-size: 0.85rem;">{branch_name}</div>
                            <div style="font-size: 0.75rem; opacity: 0.8;">{remarks}...</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No critical alerts.")

        with t_guard2:
            pending = [r for r in returns_service.get_all() if r["status"] == "Pending"][:4]
            if pending:
                for r in pending:
                    title = html.escape(str(r.get('title', 'Return')))
                    due_date = html.escape(str(r.get('due_date', '')))
                    st.markdown(f"""
                        <div class="glass-panel" style="margin-bottom: 6px; padding: 10px; border-left: 3px solid #10b981; background: #1e293b55;">
                            <div style="font-weight: 600; font-size: 0.85rem;">{title}</div>
                            <div style="font-size: 0.75rem; color: #94a3b8;">Due: {due_date}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("All returns filed.")

        # 2. Regional Celebrations (Combined Anniversary & Birthday)
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🎊 Milestone Radar")
        from src.application.services.anniversary_service import AnniversaryService
        anniv_svc = AnniversaryService()
        
        br_events = anniv_svc.get_upcoming_anniversaries(days=15)
        st_events = anniv_svc.get_staff_celebrations(days=3)
        
        if not br_events and not st_events:
            st.info("No upcoming events in the radar.")
        else:
            # Combine and sort by days_to_go
            all_events = []
            for b in br_events: all_events.append({"type": "BRANCH", "name": b["name"], "days": b["days_to_go"], "val": f"{b['years']}Y", "date": b["anniversary_date"]})
            for s in st_events: all_events.append({"type": s["type"], "name": s["name"], "days": s["days_to_go"], "val": s["type"][:1], "date": s["event_date"]})
            
            all_events.sort(key=lambda x: x["days"])
            
            for event in all_events[:6]:
                icon = "🏦" if event["type"] == "BRANCH" else ("🎂" if event["type"] == "BIRTHDAY" else "🎖️")
                color = "#3b82f6" if event["type"] == "BRANCH" else "#f59e0b"
                days_txt = "TODAY" if event["days"] == 0 else f"In {event['days']}d"
                
                name_esc = html.escape(str(event['name']))
                val_esc = html.escape(str(event['val']))
                date_esc = html.escape(event['date'].strftime('%d %b'))
                
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; padding: 8px; border-radius: 8px; border: 1px solid #ffffff11; background: #ffffff05;">
                        <div style="font-size: 1.2rem;">{icon}</div>
                        <div style="flex-grow: 1;">
                            <div style="font-size: 0.85rem; font-weight: 600;">{name_esc}</div>
                            <div style="font-size: 0.7rem; color: #94a3b8;">{date_esc} | {val_esc}</div>
                        </div>
                        <div style="font-size: 0.7rem; font-weight: 700; color: {color};">{days_txt}</div>
                    </div>
                """, unsafe_allow_html=True)

    # Footer Quick Actions
    st.divider()
    st.caption("Regional Office Cockpit V3.0 | Auto-synced with MIS Repository")
