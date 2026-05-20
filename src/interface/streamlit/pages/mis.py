from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
import datetime

from src.application.use_cases.mis.service import MISAnalyticsService
from src.core.utils.financial_year import get_fy_start
from src.domain.schemas.mis import MISFilter
from src.infrastructure.persistence.database import get_db_session
from src.interface.streamlit.components.primitives import render_action_bar, render_data_table, render_premium_metrics, render_chart_container
from src.application.services.milestone_service import MilestoneService
from src.application.services.performance_letter_service import PerformanceLetterService
from src.application.services.master_service import MasterService
from src.application.services.graphic_service import GraphicService
from src.core.paths import project_path
from src.core.utils.number_utils import format_crore as format_cr
from src.infrastructure.persistence.master_repository import MasterRepository
from src.application.services.document import DocumentService

def compile_performer_data(selected_date: datetime.date, metric_col: str, basis: str) -> tuple[list[dict], list[dict]]:
    """Compiles sorted top and bottom performers for a given metric and basis."""
    from src.application.use_cases.mis.service import MISAnalyticsService
    from src.infrastructure.persistence.budget_repository import BudgetRepository
    from src.core.utils.financial_year import get_fy_start
    import datetime

    service = MISAnalyticsService()
    budget_repo = BudgetRepository()
    
    fy_start_date = get_fy_start(selected_date)
    prev_ye_date = fy_start_date - datetime.timedelta(days=1)
    
    df = service.get_data(start_date=prev_ye_date, end_date=selected_date)
    if df.empty:
        return [], []
        
    current_month_df = df[df["DATE"].dt.date == selected_date] # type: ignore
    if current_month_df.empty:
        return [], []
        
    prev_ye_df = df[df["DATE"].dt.date == prev_ye_date] # type: ignore
    
    master_svc = MasterService()
    units = master_svc.repo.get_by_category("UNIT")
    unit_map = {int(u.code): u.name_en for u in units if u.code.isdigit()}
    
    compiled = []
    ym = selected_date.strftime("%Y-%m")
    
    for sol in current_month_df["SOL"].unique():
        if sol == 3933: continue  # Skip RO
        
        branch_data = current_month_df[current_month_df["SOL"] == sol]
        if branch_data.empty: continue
        row = branch_data.iloc[0]
        
        actual = float(row.get(metric_col.upper(), 0.0))
        
        # 1. Baseline value (prev YE)
        prev_row = prev_ye_df[prev_ye_df["SOL"] == sol]
        prev_val = float(prev_row.iloc[0].get(metric_col.upper(), 0.0)) if not prev_row.empty else 0.0
        
        # 2. Target value
        target = budget_repo.get_target(metric_col.upper(), ym, sols=[int(sol)])
        
        growth = actual - prev_val
        pct = (actual / target * 100) if target > 0 else 0.0
        
        compiled.append({
            "sol": sol,
            "name": unit_map.get(int(sol), f"SOL {sol}"),
            "actual": actual,
            "growth": growth,
            "pct": pct,
            "target": target
        })
        
    # Determine sorting order
    is_npa = "NPA" in metric_col.upper()
    reverse_sort = not is_npa
    
    if basis == "Actual Balance (₹ Cr)":
        compiled.sort(key=lambda x: x["actual"], reverse=reverse_sort)
        for c in compiled:
            c["formatted_value"] = f"{c['actual']:.2f}%" if "%" in metric_col else f"₹ {c['actual']:.2f} Cr"
    elif basis == "FY Growth (₹ Cr)":
        compiled.sort(key=lambda x: x["growth"], reverse=reverse_sort)
        for c in compiled:
            c["formatted_value"] = f"{c['growth']:+.2f}%" if "%" in metric_col else f"₹ {c['growth']:+.2f} Cr"
    elif basis == "Budget Achievement (%)":
        compiled.sort(key=lambda x: x["pct"], reverse=reverse_sort)
        for c in compiled:
            c["formatted_value"] = f"{c['pct']:.1f}%"
            
    # Format for infographic
    top_branches = [{"name": x["name"], "value": x["formatted_value"]} for x in compiled[:10]]
    
    bottom_branches = []
    last_10 = compiled[-10:]
    for i, x in enumerate(reversed(last_10)):
        actual_rank = len(compiled) - i
        bottom_branches.append({
            "name": x["name"],
            "value": x["formatted_value"],
            "rank": actual_rank
        })
    
    return top_branches, bottom_branches

@st.fragment
def render_ingestion_portal(service, letter_service):
    st.markdown("#### 📥 Live Ingestion Portal")
    st.caption("Upload daily MIS and Master feeds to keep the cockpit synchronized.")
    
    # Ingestion Cards
    up_col1, up_col2 = st.columns(2)
    
    with up_col1:
        with st.container(border=True):
            st.caption("Daily SOL-wise business figures (.xlsx)")
            mis_files = st.file_uploader(
                "Upload MIS", 
                type=["xlsx"], 
                key=st.session_state.get("uploader_key", "daily_mis"), 
                label_visibility="collapsed", 
                accept_multiple_files=True
            )
            
            if mis_files:
                if st.button("🚀 Start Ingestion", use_container_width=True, type="primary"):
                    progress_bar = st.progress(0, text="Initializing ingestion...")
                    mis_dir = project_path("data", "mis")
                    mis_dir.mkdir(parents=True, exist_ok=True)
                    
                    import os
                    # Phase 1: Saving files to disk
                    for i, mis_file in enumerate(mis_files):
                        if mis_file.size > 50 * 1024 * 1024:
                            st.error(f"File {mis_file.name} exceeds 50MB limit.")
                            continue
                            
                        current_pct = (i + 1) / (len(mis_files) * 2)
                        progress_bar.progress(
                            current_pct, 
                            text=f"📥 Saving files: {i+1} of {len(mis_files)} ({int(current_pct*100)}%)"
                        )
                        safe_name = os.path.basename(mis_file.name)
                        with open(mis_dir / safe_name, "wb") as f:
                            f.write(mis_file.getbuffer())
                    
                    # Phase 2: Processing and Syncing to DB
                    def update_progress(pct, msg):
                        total_pct = 0.5 + (pct / 2)
                        clean_msg = msg.replace("Processing ", "")
                        progress_bar.progress(
                            total_pct, 
                            text=f"⚙️ Syncing Data: {clean_msg} ({int(total_pct*100)}%)"
                        )

                    results = service.sync_database(progress_callback=update_progress)
                    
                    if results:
                        progress_bar.empty()
                        st.success(f"✅ Successfully ingested {len(results)} records!")
                        st.session_state["mis_needs_ingest"] = True
                        # Force uploader reset by changing key
                        st.session_state["uploader_key"] = datetime.datetime.now().timestamp()
                        st.rerun()

    with up_col2:
        with st.container(border=True):
            st.markdown("##### 🎯 Target & Budget Feed")
            st.caption("Update annual goals and SOL targets (.csv)")
            budget_file = st.file_uploader("Upload Budget", type=["csv"], key="daily_budget", label_visibility="collapsed")
            if budget_file:
                if budget_file.size > 10 * 1024 * 1024:
                    st.error("Budget file exceeds 10MB limit.")
                else:
                    with st.spinner("Syncing targets..."):
                        target_path = project_path("files", "Budget3.csv")
                        with open(target_path, "wb") as f:
                            f.write(budget_file.getbuffer())
                        letter_service.budget_repo.sync_if_needed()
                        st.success("Regional targets updated successfully!")
                        st.rerun()

    st.divider()
    h_title_col, h_action_col = st.columns([3, 1])
    with h_title_col:
        st.markdown("##### 📜 Ingestion History")
    
    # Show last 10 archived MIS files for bulk management
    mis_archive = project_path("data", "mis", "archive")
    if mis_archive.exists():
        history_files = sorted(list(mis_archive.glob("*.xlsx")), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
        if history_files:
            to_delete = []
            
            with h_action_col:
                # Multi-action buttons
                if st.button("🗑️ Bulk Delete", use_container_width=True, type="secondary", help="Delete selected files"):
                    st.session_state["show_bulk_confirm"] = True
            
            # Bulk Confirmation Dialog
            if st.session_state.get("show_bulk_confirm"):
                with st.container(border=True):
                    st.warning("⚠️ Are you sure you want to delete selected data feeds?")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Confirm Deletion", use_container_width=True):
                        files_to_del = st.session_state.get("mis_selected_files", [])
                        progress_bar = st.progress(0, text="Initializing batch removal...")
                        deleted_count = 0
                        
                        for i, f_name in enumerate(files_to_del):
                            pct = (i + 1) / len(files_to_del)
                            progress_bar.progress(
                                pct,
                                text=f"🗑️ Deleting: {f_name} ({i+1}/{len(files_to_del)}) - {int(pct*100)}%"
                            )
                            if service.delete_mis_file(f_name):
                                deleted_count += 1
                                
                        progress_bar.empty()
                        st.success(f"Successfully removed {deleted_count} data feeds.")
                        st.session_state["show_bulk_confirm"] = False
                        st.session_state["mis_selected_files"] = []
                        st.rerun()
                    if c2.button("❌ Cancel", use_container_width=True):
                        st.session_state["show_bulk_confirm"] = False
                        st.rerun()

            # History List with Checkboxes
            selected_files = st.session_state.get("mis_selected_files", [])
            
            for f in history_files:
                h_time = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%d-%b %H:%M")
                h_col1, h_col2 = st.columns([0.1, 4.9])
                with h_col1:
                    is_selected = st.checkbox("", key=f"chk_{f.name}", value=f.name in selected_files, label_visibility="collapsed")
                    if is_selected and f.name not in selected_files:
                        selected_files.append(f.name)
                    elif not is_selected and f.name in selected_files:
                        selected_files.remove(f.name)
                with h_col2:
                    st.caption(f"✅ **{f.name}** (Ingested: {h_time})")
            
            st.session_state["mis_selected_files"] = selected_files
            
            if st.button("🧨 Clear Entire Archive", type="secondary", use_container_width=True):
                all_files = list(mis_archive.glob("*.xlsx"))
                progress_bar = st.progress(0, text="🧨 Wiping entire archive...")
                for i, f in enumerate(all_files):
                    pct = (i + 1) / len(all_files)
                    progress_bar.progress(
                        pct, 
                        text=f"💥 Removing: {f.name} ({i+1}/{len(all_files)}) - {int(pct*100)}%"
                    )
                    service.delete_mis_file(f.name)
                progress_bar.empty()
                st.success("Entire archive cleared!")
                st.rerun()
        else:
            st.write("No ingestion history available.")
    
    with st.expander("🛠️ Advanced Maintenance"):
        st.markdown("##### 🧨 Targeted Data Removal")
        st.caption("Surgically remove all records and milestones for a specific reporting date.")
        c1, c2 = st.columns([2, 1])
        with c1:
            target_del_date = st.date_input("Date to Wipe", value=None, min_value=datetime.date(2024, 1, 1), key="wipe_date")
        with c2:
            st.write("") # Spacer
            if st.button("🗑️ Wipe Date", use_container_width=True, type="secondary"):
                if target_del_date:
                    with st.spinner(f"Wiping {target_del_date}..."):
                        r_cnt, m_cnt = service.delete_records_by_date(target_del_date)
                        st.success(f"Successfully wiped {r_cnt} records and {m_cnt} milestones for {target_del_date}.")
                        service.build_snapshot.clear()
                        st.rerun()
                else:
                    st.error("Select a date.")

def render() -> None:
    service = MISAnalyticsService()
    # Temporary cache clear to ensure the new caching and ADV logic is applied
    if "global_cache_reset_v3" not in st.session_state:
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state["global_cache_reset_v3"] = True
        st.rerun()

    letter_service = PerformanceLetterService()
    # 1. Page Title
    render_action_bar("Regional MIS Analytics", ["Market Share", "Budget Tracking", "NPA Surveillance"])
    
    # ─── UPLOAD FEEDBACK ──────────────────────────────────────────────────
    if "mis_upload_results" in st.session_state:
        for res in st.session_state["mis_upload_results"]:
            st.success(f"✅ **Update Successful!** Processed `{res['filename']}`. Data for **{res['dates']}** ({res['count']} units) has been updated in the regional database.")
        del st.session_state["mis_upload_results"]
    
    # ─── REGIONAL DATA FEED (DAILY INGESTION) ──────────────────────────────
    with st.expander("📡 Regional Data Feed", expanded=False):
        render_ingestion_portal(service, letter_service)
    
    # ─── BASE DATA LOAD ────────────────────────────────────────────────────
    dates = service.get_available_dates()
    if not dates:
        st.error("No MIS data found. Please use the Maintenance Hub above to upload MIS files.")
        return
        
    sols = service.get_available_sols()
    
    # 2. Global Filters
    
    # SOL to Branch Name Mapping
    repo = MasterRepository()
    units = repo.get_by_category("UNIT")
    unit_map = {int(u.code): f"{u.code} - {u.name_en}" for u in units if u.code.isdigit()}
    
    col_d, col_b = st.columns(2)
    with col_d:
        selected_date = st.selectbox("Reporting Date", dates, index=len(dates) - 1)
    with col_b:
        selected_sols = st.multiselect(
            "Unit Focus", 
            options=sols, 
            default=[],
            format_func=lambda x: unit_map.get(x, f"SOL {x}")
        )

    # 3. Dynamic Snapshot Generation
    # Use dictionary for caching compatibility in build_snapshot
    snapshot = service.build_snapshot({"selected_date": selected_date, "sols": selected_sols})
    if not snapshot:
        st.warning("No data found for this selection.")
        return

    # Glassmorphic KPI Row
    render_premium_metrics(snapshot.kpis)
    
    st.markdown("<br>", unsafe_allow_html=True)

    frame = pd.DataFrame(snapshot.rows)
    # Filter for numeric columns that aren't IDs or Dates
    excluded_cols = {"SOL", "DATE", "SNO", "ID", "YEAR", "MONTH", "CD RATIO", "NPA %"}
    metric_options = [c for c in frame.columns if frame[c].dtype in ['float64', 'int64'] and c.upper() not in excluded_cols]
    
    # Advanced Performance Tracking
    with st.expander("📈 Advanced Budget Gap Analysis", expanded=True):
        metric_to_track = st.selectbox("Select Parameter to Analyze", sorted(metric_options), index=sorted(metric_options).index("ADV") if "ADV" in metric_options else 0)
        perf = service.get_performance_metrics(selected_date, metric_to_track, sols=selected_sols)
        
        # Advanced Performance Tracking

        if perf:
            st.markdown("### 🎯 Executive Budget Gap Summary")
            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1:
                growth_color = "#10b981" if perf['fy_growth'] >= 0 else "#ef4444"
                st.markdown(f"""
                    <div class="glass-panel" style="border-top: 4px solid {growth_color}; background: #0f172a; border-radius: 12px; padding: 20px;">
                        <div style="font-size: 0.75rem; color: #94a3b8; letter-spacing: 0.1rem; font-weight: 700; text-transform: uppercase;">FY GROWTH</div>
                        <div style="font-size: 2.2rem; font-weight: 800; color: #ffffff; margin: 12px 0;">{format_cr(perf['fy_growth'])}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: {growth_color}; font-weight: 700; font-size: 1rem;">{'↑' if perf['fy_growth'] >= 0 else '↓'} {abs(perf['fy_growth_pct']):.2f}%</span>
                            <span style="font-size: 0.85rem; color: #94a3b8; font-weight: 600;">Base: {format_cr(perf['fy_start_actual'])}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with p_col2:
                gap = perf['gap_current_month']
                gap_color = "#ef4444" if gap > 0 else "#10b981"
                st.markdown(f"""
                    <div class="glass-panel" style="border-top: 4px solid {gap_color}; background: #0f172a; border-radius: 12px; padding: 20px;">
                        <div style="font-size: 0.75rem; color: #94a3b8; letter-spacing: 0.1rem; font-weight: 700; text-transform: uppercase;">MONTHLY GAP</div>
                        <div style="font-size: 2.2rem; font-weight: 800; color: {gap_color}; margin: 12px 0;">{format_cr(abs(gap))}</div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600;">
                            <span style="color: #f8fafc;">Actual: {format_cr(perf['current_actual'])}</span>
                            <span style="color: #94a3b8;">Target: {format_cr(perf['targets']['month'])}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with p_col3:
                gap_fy = perf['gap_fy']
                gap_fy_color = "#ef4444" if gap_fy > 0 else "#10b981"
                st.markdown(f"""
                    <div class="glass-panel" style="border-top: 4px solid {gap_fy_color}; background: #0f172a; border-radius: 12px; padding: 20px;">
                        <div style="font-size: 0.75rem; color: #94a3b8; letter-spacing: 0.1rem; font-weight: 700; text-transform: uppercase;">ANNUAL GAP</div>
                        <div style="font-size: 2.2rem; font-weight: 800; color: {gap_fy_color}; margin: 12px 0;">{format_cr(abs(gap_fy))}</div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600;">
                            <span style="color: #f8fafc;">Actual: {format_cr(perf['current_actual'])}</span>
                            <span style="color: #94a3b8;">Target: {format_cr(perf['targets']['fy'])}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # Visualization Layer
    tabs = st.tabs(["📊 Business Trends", "🏦 Advances Portfolio", "🏆 Milestones Record", "🎯 Budget Matrix", "📬 Budget Communication", "🎨 Infographics Portal"])
    
    with tabs[0]:
        col_chart, col_table = st.columns([1.5, 1])
        
        history = pd.DataFrame(snapshot.history_rows)
        if not history.empty:
            history["DATE"] = pd.to_datetime(history["DATE"])
            fy_start = pd.to_datetime(get_fy_start(selected_date))
            
            # Locate the baseline date to ensure the starting figure is plotted
            prev_fy_data = history[history["DATE"] < fy_start]
            if not prev_fy_data.empty:
                baseline_date = prev_fy_data["DATE"].max()
                history = history[history["DATE"] >= baseline_date]
            else:
                history = history[history["DATE"] >= fy_start]

        with col_chart:
            if not history.empty:
                st.markdown("#### 📈 Dynamic Business Trend (Current FY)")
                # Multi-line chart: Advances vs Deposits
                trend = history.groupby("DATE", as_index=False)[["ADV", "TOTAL DEPOSITS"]].sum()
                fig = px.line(trend, x="DATE", y=["ADV", "TOTAL DEPOSITS"], 
                            template="plotly_dark", color_discrete_sequence=["#3b82f6", "#10b981"])
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title=None)
                st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.markdown("#### 🏢 Unit Hierarchy")
            frame = pd.DataFrame(snapshot.rows)
            if not frame.empty:
                # Add Branch Name column for display
                frame["Branch"] = frame["SOL"].map(lambda x: unit_map.get(int(x), f"SOL {x}") if pd.notnull(x) else "Unknown")
                st.dataframe(frame[["Branch", "ADV", "TOTAL DEPOSITS", "NPA %"]].sort_values("ADV", ascending=False).head(500), 
                             hide_index=True, use_container_width=True)
            
    with tabs[1]:
        from src.application.services.advances_service import AdvancesService
        adv_service = AdvancesService()
        st.subheader("🏦 Advances Portfolio Risk Analysis")
        
        # 1. Selection and Persistence Logic
        avail_dates = adv_service.get_available_dates()
        col_sel, col_up = st.columns([1, 1.5])
        
        with col_sel:
            selected_report_dt = st.selectbox(
                "Select Saved Report", 
                options=avail_dates, 
                format_func=lambda x: x.strftime('%d-%b-%Y'),
                help="Select a previously uploaded and processed portfolio report."
            )

        with col_up:
            uploaded_adv = st.file_uploader("Upload New Advances File", type=["xlsx", "xls", "csv"], key="mis_adv_upload")
        
        adv_df = pd.DataFrame()
        
        if uploaded_adv:
            with st.spinner("Processing & Saving portfolio..."):
                # Process the new data
                adv_df = adv_service.process_data(uploaded_adv)
                # Persist to database
                saved_date = adv_service.save_to_db(adv_df)
                if saved_date:
                    st.success(f"Successfully processed and saved report for {saved_date.strftime('%d-%b-%Y')}")
                    # Set as current view
                    selected_report_dt = saved_date
                else:
                    st.error("Failed to save report.")
        elif selected_report_dt:
            with st.spinner("Loading stored report..."):
                adv_df = adv_service.get_stored_data(selected_report_dt)
                # Normalize column names for the stats engine (since DB stores them lowercase/standardized)
                # But our stats engine expects uppercase normalized names from process_data.
                # Actually, AdvancesRepository stores them with specific lowercase names.
                # Let's map them back to the expected names for the stats engine.
                reverse_mapping = {
                    'branch_code': 'BRANCH_CODE',
                    'ac_name': 'AC_NAME',
                    'foracid': 'FORACID',
                    'schm_code': 'SCHM_CODE',
                    'gl_sub_cd': 'GL_SUB_CD',
                    'open_dt': 'OPEN_DT_NORM',
                    'limit_cr': 'LIMIT_CR',
                    'balance_cr': 'BALANCE_CR',
                    'risk_category': 'RISK_CATEGORY',
                    'l1_category': 'L1_CATEGORY',
                    'l2_sector': 'L2_SECTOR',
                    'l3_scheme': 'L3_SCHEME',
                    'priority_type': 'PRIORITY_TYPE'
                }
                adv_df.rename(columns=reverse_mapping, inplace=True)
                # Ensure date column is datetime
                adv_df['OPEN_DT_NORM'] = pd.to_datetime(adv_df['OPEN_DT_NORM'])
                # Add report_dt for stats extraction
                adv_df['REPORT_DT'] = selected_report_dt.strftime('%Y%m%d')

        if not adv_df.empty:
            stats = adv_service.get_summary_stats(adv_df)
            
            from src.core.utils.number_utils import format_indian_number
            # Metric Row (Glassmorphic)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Accounts", f"{stats['total_count']:,}")
            m2.metric("Portfolio", f"₹ {format_indian_number(stats['total_balance_cr'])} Cr")
            m3.metric("NPA", f"₹ {format_indian_number(stats.get('risk_summary', {}).get('NPA', {}).get('sum', 0))} Cr")
            m4.metric("SMA-2", f"₹ {format_indian_number(stats.get('risk_summary', {}).get('SMA-2', {}).get('sum', 0))} Cr")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Sanctions Overview (Temporal)
            s_vals = stats.get('sanctions', {})
            st.markdown("#### 🚀 Sanction Momentum")
            s1, s2, s3 = st.columns(3)
            s1.metric("Month", f"₹ {format_indian_number(s_vals.get('month', 0))} Cr")
            s2.metric("Quarter", f"₹ {format_indian_number(s_vals.get('quarter', 0))} Cr")
            s3.metric("FY Total", f"₹ {format_indian_number(s_vals.get('fy', 0))} Cr")

            # Granular Breakup
            with st.expander("📊 Detailed Sanction Breakup by Category & Scheme", expanded=True):
                breakup = stats.get('sanction_breakup', {})
                breakup_data = []
                for grp, vals in breakup.items():
                    breakup_data.append({
                        'Category': vals['category'],
                        'Subdivision': vals['subdivision'],
                        'Mth Cnt': vals['month_count'],
                        'Mth (Cr)': vals['month_amt'],
                        'Qtr Cnt': vals['quarter_count'],
                        'Qtr (Cr)': vals['quarter_amt'],
                        'FY Cnt': vals['fy_count'],
                        'FY (Cr)': vals['fy_amt']
                    })
                
                b_df = pd.DataFrame(breakup_data)
                if not b_df.empty:
                    # Sort by Category then FY Total
                    b_df = b_df.sort_values(['Category', 'FY (Cr)'], ascending=[True, False])
                    st.table(b_df.style.format({
                        'Mth (Cr)': lambda x: format_indian_number(float(x) if pd.notnull(x) else 0.0),
                        'Qtr (Cr)': lambda x: format_indian_number(float(x) if pd.notnull(x) else 0.0),
                        'FY (Cr)': lambda x: format_indian_number(float(x) if pd.notnull(x) else 0.0),
                        'Mth Cnt': '{:,}',
                        'Qtr Cnt': '{:,}',
                        'FY Cnt': '{:,}'
                    }))
                    
                    # Download Branch-wise reports
                    st.markdown("---")
                    st.markdown("##### 📥 Download Branch-wise Analysis")
                    d_col1, d_col2, d_col3 = st.columns(3)
                    
                    with d_col1:
                        m_report = adv_service.generate_branch_wise_sanction_report(adv_df, selected_report_dt, period='month')
                        if m_report:
                            st.download_button(
                                label="This Month",
                                data=m_report,
                                file_name=f"Sanctions_MTD_{selected_report_dt.strftime('%b_%Y')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                    
                    with d_col2:
                        pm_report = adv_service.generate_branch_wise_sanction_report(adv_df, selected_report_dt, period='prev_month')
                        if pm_report:
                            st.download_button(
                                label="Prev Month",
                                data=pm_report,
                                file_name=f"Sanctions_PrevMth_{selected_report_dt.strftime('%b_%Y')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                    
                    with d_col3:
                        fy_report = adv_service.generate_branch_wise_sanction_report(adv_df, selected_report_dt, period='fy')
                        if fy_report:
                            st.download_button(
                                label="Full FY",
                                data=fy_report,
                                file_name=f"Sanctions_FY_{selected_report_dt.strftime('%Y')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### Category Distribution")
                cat_df = pd.DataFrame(list(stats['by_category'].items()), columns=['Category', 'Balance (Cr)'])
                fig_cat = px.pie(cat_df, values='Balance (Cr)', names='Category', hole=.4, template="plotly_dark")
                st.plotly_chart(fig_cat, use_container_width=True)
            
            with col_b:
                st.markdown("#### Asset Quality Mix")
                risk_df = pd.DataFrame([{'Risk': k, 'Balance': v['sum']} for k, v in stats['risk_summary'].items()])
                fig_risk = px.bar(risk_df, x='Risk', y='Balance', template="plotly_dark", color='Risk')
                st.plotly_chart(fig_risk, use_container_width=True)

            st.markdown("#### Sector Breakdown")
            sector_df = pd.DataFrame([{'Sector': k, 'Count': v['count'], 'Balance (Cr)': v['sum']} for k, v in stats['by_sector'].items()])
            st.dataframe(sector_df.sort_values('Balance (Cr)', ascending=False).head(500), use_container_width=True, hide_index=True)
        else:
            st.warning("Please upload an Advances file to begin analysis.")

    with tabs[2]:
        col_title, col_pdf = st.columns([3, 1])
        with col_title:
            st.subheader("🏆 Business Milestones Record")
        with col_pdf:
            doc_service = DocumentService()
            
            # Prepare summary for PDF (Count by Parameter)
            params_avail = MilestoneService.PARAMETERS
            summary_data = []
            milestone_list = snapshot.milestones or []
            
            for p in params_avail:
                p_milestones = [m for m in milestone_list if m["parameter"] == p]
                count_50 = sum(1 for m in p_milestones if m["value"] >= 50)
                count_100 = sum(1 for m in p_milestones if m["value"] >= 100)
                count_150 = sum(1 for m in p_milestones if m["value"] >= 150)
                count_200 = sum(1 for m in p_milestones if m["value"] >= 200)
                
                summary_data.append({
                    "Parameter": p,
                    "50Cr+": count_50,
                    "100Cr+": count_100,
                    "150Cr+": count_150,
                    "200Cr+": count_200,
                    "Total Milestones": len(p_milestones)
                })
            
            if st.button("📄 Prepare PDF Report", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    pdf_bytes = doc_service.generate_milestones_pdf(
                        snapshot.milestones, 
                        summary_data, 
                        str(snapshot.selected_date)
                    )
                    st.session_state["milestone_pdf"] = pdf_bytes
            
            if "milestone_pdf" in st.session_state:
                st.download_button(
                    "📥 Download Report",
                    data=st.session_state["milestone_pdf"],
                    file_name=f"Milestone_Report_{snapshot.selected_date}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        st.info("Tracks branches that have crossed 50Cr, 100Cr, 150Cr, 200Cr, 250Cr... milestones.")
        
        # Monthly Breakthroughs Section
        if snapshot.milestone_breakthroughs:
            with st.container(border=True):
                col_bt, col_btn = st.columns([3, 1.5])
                with col_bt:
                    # Determine the month for the title
                    target_month_name = snapshot.selected_date.strftime("%B %Y")
                    st.markdown(f"#### 🌟 Monthly Breakthroughs ({target_month_name})")
                    st.caption(f"Branches that crossed a NEW 50Cr-increment threshold during {target_month_name}.")
                with col_btn:
                    # Resolve Signatory
                    exec_list = MasterService().get_ro_executives()
                    exec_options = {e["roll"]: e["name"] for e in exec_list}
                    selected_sig_roll_ms = st.selectbox("Signing Authority", options=list(exec_options.keys()), format_func=lambda x: exec_options[x], key="ms_sig")
                    selected_signatory = next((e for e in exec_list if e["roll"] == selected_sig_roll_ms), None)

                    if st.button("✅ Finalize & Generate Letters", use_container_width=True):
                        with st.spinner("Saving breakthroughs and preparing letters..."):
                            saved_count = service.save_milestone_achievements(snapshot.milestone_breakthroughs)
                            st.success(f"Successfully recorded {saved_count} new breakthroughs!")
                            
                            # Generate letters and posters
                            graphic_srv = GraphicService()
                            
                            import io, zipfile
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, "w") as zf:
                                for i, b in enumerate(snapshot.milestone_breakthroughs):
                                    # PDF Letter
                                    pdf = doc_service.generate_milestone_appreciation(b, selected_signatory or {})
                                    pdf_name = f"Appreciation_{b['branch_name'].replace(' ', '_')}_{b['parameter']}.pdf"
                                    zf.writestr(f"Letters/{pdf_name}", pdf)
                                    
                                    # Social Media Poster
                                    img_bytes = graphic_srv.generate_milestone_poster(b)
                                    img_name = f"Poster_{b['branch_name'].replace(' ', '_')}_{b['parameter']}.png"
                                    zf.writestr(f"Posters/{img_name}", img_bytes)
                            
                            st.session_state["breakthrough_zip"] = zip_buffer.getvalue()

                    if "breakthrough_zip" in st.session_state:
                        st.download_button(
                            "📥 Download Appreciation Kit",
                            data=st.session_state["breakthrough_zip"],
                            file_name=f"Recognition_Kit_{snapshot.selected_date}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

                b_df = pd.DataFrame(snapshot.milestone_breakthroughs)
                cols_to_show = ["branch_name", "parameter", "previous_value", "value", "milestone"]
                b_display = b_df[cols_to_show].copy()
                b_display["previous_value"] = b_display["previous_value"].map(lambda x: f"{x:.2f}")
                b_display["value"] = b_display["value"].map(lambda x: f"{x:.2f}")

                p_dt = b_df["prev_date"].iloc[0].strftime("%d-%b") if "prev_date" in b_df.columns and not b_df.empty else "Prev"
                c_dt = b_df["date"].iloc[0].strftime("%d-%b") if "date" in b_df.columns and not b_df.empty else "Curr"
                b_display.columns = ["Branch", "Parameter", f"Value {p_dt} (Cr)", f"Value {c_dt} (Cr)", "New Milestone"]
                st.table(b_display)
        
        if snapshot.milestones:
            m_df_raw = pd.DataFrame(snapshot.milestones)
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                selected_param = st.multiselect("Filter Parameters", params_avail, default=[])
            with col_f2:
                levels_avail = sorted(m_df_raw["milestone"].unique())
                selected_levels = st.multiselect("Filter Milestones", levels_avail, default=[])

            filtered_df = m_df_raw.copy()
            if selected_param:
                filtered_df = filtered_df[filtered_df["parameter"].isin(selected_param)]
            if selected_levels:
                filtered_df = filtered_df[filtered_df["milestone"].isin(selected_levels)]

            if not filtered_df.empty:
                st.markdown(f"#### Milestones Inventory")
                display_df = filtered_df[["sol", "branch_name", "parameter", "value", "milestone"]].copy()
                display_df.columns = ["SOL", "Branch", "Parameter", "Value (Cr)", "Milestone"]
                display_df["Value (Cr)"] = display_df["Value (Cr)"].map(lambda x: f"{x:.2f}")
                st.dataframe(display_df.sort_values(["Milestone", "Value (Cr)"], ascending=False).head(500), hide_index=True, use_container_width=True)
            
            st.divider()
            st.markdown("#### Achievement Heatmap (Parameter vs Level)")
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df.sort_values("Total Milestones", ascending=False).head(500), hide_index=True, use_container_width=True)

    with tabs[3]:
        st.subheader("🎯 Monthly Budget Matrix")
        st.caption("Cumulative monthly targets distributed across the selected branches.")
        
        current_fy_start = get_fy_start(selected_date)
        
        budget_df = letter_service.budget_repo.get_monthly_targets(sols=selected_sols if selected_sols else sols, fy_start=current_fy_start)
        
        if not budget_df.empty:
            formatted_df = budget_df.copy()
            for col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(lambda x: format_cr(x) if pd.notnull(x) else "-")
            st.dataframe(formatted_df.head(500), use_container_width=True)
            
            csv = budget_df.to_csv().encode('utf-8')
            st.download_button(
                label="📥 Download Budget Matrix",
                data=csv,
                file_name=f"Budget_Matrix_{current_fy_start.year}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No budget data found for the selected branches in the current financial year.")

    with tabs[4]:
        letter_service = PerformanceLetterService()
        
        st.subheader("📬 Regional Communication Center")
        
        # --- Section 1: Budget Communication ---
        st.markdown("### 🎯 Annual Budget Communication")
        
        status = letter_service.budget_repo.get_sync_status()
        st.caption(f"🛡️ **Data Maintenance:** Last synced on {status['last_sync']} | FYs available: {', '.join(status['fy_ranges'])}")
        
        st.info("Generate formal budget communication letters for all parameters defined in the registry.")
        
        # FY & Communication Date
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            selected_fy = st.selectbox("Target Fiscal Year", options=status["fy_ranges"], index=len(status["fy_ranges"])-1 if status["fy_ranges"] else 0)
        with fcol2:
            comm_date = st.date_input("Date of Communication", value=datetime.date.today())
        
        # Convert selected_fy (e.g. "2026-27") to a date (2026-04-01) for target retrieval
        try:
            fy_start_year = int(selected_fy.split("-")[0])
            fy_ref_date = datetime.date(fy_start_year, 4, 1)
        except:
            fy_ref_date = selected_date
            
        exec_list = MasterService().get_ro_executives()
        exec_options = {e["roll"]: e["name"] for e in exec_list}
        selected_sig_roll = st.selectbox("Signing Authority (Budget)", options=list(exec_options.keys()), format_func=lambda x: exec_options[x], key="budget_sig")
        
        if st.button("🚀 Generate Budget Letters (ZIP)", use_container_width=True):
            budget_data = letter_service.get_budget_communication_data(fy_ref_date)
            if not budget_data:
                st.error(f"No budget data found for {selected_fy}.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(pct, msg):
                    try:
                        progress_bar.progress(pct)
                        status_text.text(msg)
                        return True
                    except: return False
                
                signatory_profile = letter_service.doc_service._resolve_staff_profile(str(selected_sig_roll) if selected_sig_roll else "")
                formatted_comm_date = comm_date.strftime("%d.%m.%Y")
                zip_bytes = letter_service.generate_budget_zip(
                    budget_data, 
                    signatory_profile, 
                    progress_callback=update_progress,
                    comm_date=formatted_comm_date
                )
                
                progress_bar.empty()
                status_text.empty()
                if zip_bytes:
                    st.success(f"Generated budget letters for {len(budget_data)} branches!")
                    st.download_button("📥 Download Budget Letters ZIP", data=zip_bytes, file_name=f"Budget_Communication_{selected_fy}.zip", mime="application/zip", use_container_width=True)

        st.divider()
        
        # --- Section 2: Performance Letters ---
        perf_header_col1, perf_header_col2 = st.columns([3, 1])
        with perf_header_col1:
            st.markdown("### 📈 Monthly Performance Communication")
            st.caption("Generate mass appreciation and explanation letters based on budget performance.")
        
        with perf_header_col2:
            # Group available dates by Month-Year for selection
            month_options = {}
            for d in reversed(dates):
                m_key = d.strftime("%B %Y")
                if m_key not in month_options:
                    month_options[m_key] = d # Keep the latest date for that month
            
            # Default to the month of the globally selected date
            current_m_key = selected_date.strftime("%B %Y")
            default_idx = list(month_options.keys()).index(current_m_key) if current_m_key in month_options else 0
            
            selected_perf_month_key = st.selectbox("Target Month", options=list(month_options.keys()), index=default_idx, key="perf_month_picker")
            perf_date = month_options[selected_perf_month_key]

        performance_data = letter_service.get_branch_performance(perf_date)
        
        if performance_data:
            with st.expander("📝 Review Monthly Performance Status", expanded=False):
                for p in performance_data:
                    all_achievements = []
                    all_declines = []
                    for g_data in p.get("groups", {}).values():
                        all_achievements.extend(g_data.get("achievements", []))
                        all_declines.extend(g_data.get("declines", []))

                    status_col, name_col, details_col = st.columns([1, 2, 4])
                    with status_col:
                        if all_achievements and not all_declines: st.success("EXCELLENT")
                        elif all_achievements and all_declines: st.warning("MIXED")
                        else: st.error("ACTION REQ")
                    with name_col: st.markdown(f"**{p['branch_name']}** ({p['sol']})")
                    with details_col:
                        ach_tags = [f"{a['parameter']} ({a['pct']:.0f}%)" for a in all_achievements[:3]]
                        dec_tags = [f"{a['parameter']} ({a['pct']:.0f}%)" for a in all_declines[:3]]
                        if ach_tags: st.markdown(f"✅ {', '.join(ach_tags)}")
                        if dec_tags: st.markdown(f"⚠️ {', '.join(dec_tags)}")

            selected_sig_roll_perf = st.selectbox("Signing Authority (Performance)", options=list(exec_options.keys()), format_func=lambda x: exec_options[x], key="perf_sig")
            selected_signatory = next((e for e in exec_list if e["roll"] == selected_sig_roll_perf), None)

            # --- INTERRUPTIBLE GENERATION LOGIC (V2: STATE-PERSISTENT) ---
            if "zip_gen_state" not in st.session_state:
                st.session_state.zip_gen_state = {"active": False, "stopped": False, "data": None, "current_idx": 0}
            if "zip_gen_accumulator" not in st.session_state:
                st.session_state.zip_gen_accumulator = [] # List of (filename, bytes)

            gen_col, stop_col = st.columns([3, 1])
            
            with gen_col:
                if not st.session_state.zip_gen_state["active"] and not st.session_state.zip_gen_accumulator:
                    if st.button("📦 Generate All Performance Letters (ZIP)", use_container_width=True):
                        if not selected_signatory:
                            st.error("Please select a signatory.")
                        else:
                            st.session_state.zip_gen_state = {"active": True, "stopped": False, "data": None, "current_idx": 0}
                            st.session_state.zip_gen_accumulator = []
                            st.rerun()
                elif not st.session_state.zip_gen_state["active"] and st.session_state.zip_gen_accumulator:
                    # Partial data exists, show download or reset
                    import io, zipfile
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for fname, fdata in st.session_state.zip_gen_accumulator:
                            zf.writestr(fname, fdata)
                    
                    st.session_state.zip_gen_state["data"] = zip_buffer.getvalue()
                    
                    st.download_button(
                        f"📥 Download Partial Kit ({len(st.session_state.zip_gen_accumulator)} letters)", 
                        data=st.session_state.zip_gen_state["data"], 
                        file_name=f"Performance_Letters_PARTIAL_{snapshot.selected_date}.zip", 
                        mime="application/zip", 
                        use_container_width=True
                    )
                    if st.button("🔄 Start New Generation", use_container_width=True):
                        st.session_state.zip_gen_accumulator = []
                        st.session_state.zip_gen_state = {"active": False, "stopped": False, "data": None, "current_idx": 0}
                        st.rerun()

            with stop_col:
                if st.session_state.zip_gen_state["active"]:
                    if st.button("🛑 STOP", type="primary", use_container_width=True):
                        st.session_state.zip_gen_state["active"] = False
                        st.session_state.zip_gen_state["stopped"] = True
                        st.rerun()

            if st.session_state.zip_gen_state["active"]:
                status_placeholder = st.empty()
                progress_bar = st.progress(0)
                
                total = len(performance_data)
                # Resume from current_idx
                for i in range(st.session_state.zip_gen_state["current_idx"], total):
                    st.session_state.zip_gen_state["current_idx"] = i
                    branch = performance_data[i]
                    pct = (i + 1) / total
                    status_placeholder.markdown(f"**⚡ Processing Branch {i+1}/{total}:** `{branch['branch_name']}`")
                    progress_bar.progress(pct)
                    
                    # Generate letters for this branch
                    for group_name, data in branch["groups"].items():
                        if data["achievements"]:
                            payload = {**branch, "group_name": group_name, "achievements": data["achievements"], "signatory": selected_signatory}
                            pdf = letter_service.doc_service.generate_performance_appreciation(payload)
                            folder = f"Appreciation_Letters/{group_name.replace(' ', '_')}"
                            fname = f"{folder}/Appr_{branch['sol']}_{group_name.replace(' ', '_')}.pdf"
                            st.session_state.zip_gen_accumulator.append((fname, pdf))

                        if data["declines"]:
                            payload = {**branch, "group_name": group_name, "declines": data["declines"], "signatory": selected_signatory}
                            pdf = letter_service.doc_service.generate_explanation_letter(payload)
                            folder = f"Explanation_Letters/{group_name.replace(' ', '_')}"
                            fname = f"{folder}/Expl_{branch['sol']}_{group_name.replace(' ', '_')}.pdf"
                            st.session_state.zip_gen_accumulator.append((fname, pdf))
                
                # Finished normally
                st.session_state.zip_gen_state["active"] = False
                st.rerun()
        else:
            st.info("No performance data available.")

    with tabs[5]:
        st.subheader("🎨 Performance Infographics Portal")
        st.caption("Generate, preview, and download premium corporate infographics of regional top and bottom performers.")
        
        # Deduplicate month list and map to latest date in that month
        month_to_latest_date = {}
        for d in dates:
            if d is None:
                continue
            month_key = (d.year, d.month)
            if month_key not in month_to_latest_date or d > month_to_latest_date[month_key]:
                month_to_latest_date[month_key] = d
                
        # Sorted unique months descending (newest first)
        unique_months = sorted(list(month_to_latest_date.keys()), reverse=True)
        
        # Resolve default month index
        default_month_key = (selected_date.year, selected_date.month)
        default_idx = unique_months.index(default_month_key) if default_month_key in unique_months else 0
        
        c_date, c_metric = st.columns(2)
        with c_date:
            selected_month_key = st.selectbox(
                "Infographic Reporting Month",
                options=unique_months,
                index=default_idx,
                format_func=lambda x: datetime.date(x[0], x[1], 1).strftime("%B %Y"),
                key="inf_month_key"
            )
        
        selected_inf_date = month_to_latest_date[selected_month_key]
        
        inf_metric_opts = {
            "ADV": "Total Advances (ADV)",
            "TOTAL DEPOSITS": "Total Deposits",
            "CASA": "CASA Deposits",
            "JEWEL LOAN": "Jewel Loan Portfolio",
            "AGRI": "Core Agri Advances",
            "MSME": "MSME Portfolio",
            "RETAIL": "Retail Portfolio"
        }
        
        available_metrics = [m for m in metric_options if m in inf_metric_opts]
        if not available_metrics:
            available_metrics = ["ADV", "TOTAL DEPOSITS", "CASA"]
            
        with c_metric:
            selected_inf_metric = st.selectbox(
                "Infographic Metric",
                options=available_metrics,
                format_func=lambda x: inf_metric_opts.get(x, x),
                key="inf_metric"
            )
            
        c_basis, c_title = st.columns(2)
        with c_basis:
            selected_inf_basis = st.selectbox(
                "Ranking Basis",
                options=["Actual Balance (₹ Cr)", "FY Growth (₹ Cr)", "Budget Achievement (%)"],
                key="inf_basis"
            )
        with c_title:
            campaign_title = st.text_input("Campaign Header Title", value="Dindigul Region", key="campaign_title")
            
        campaign_sub = st.text_input("Campaign Sub-Title", value="Performance League", key="campaign_sub")
            
        if st.button("🎨 Generate Infographic Poster", type="primary", use_container_width=True):
            with st.spinner("Compiling database records and generating high-resolution poster..."):
                top_branches, bottom_branches = compile_performer_data(
                    selected_inf_date, 
                    selected_inf_metric, 
                    selected_inf_basis
                )
                
                if not top_branches:
                    st.error("No performer records compiled. Please verify data exists for this date.")
                else:
                    graphic_srv = GraphicService()
                    month_str = selected_inf_date.strftime("%B %Y")
                    metric_label = inf_metric_opts.get(selected_inf_metric, selected_inf_metric)
                    
                    img_bytes = graphic_srv.generate_performance_infographic(
                        campaign_title,
                        campaign_sub,
                        metric_label,
                        selected_inf_basis,
                        month_str,
                        top_branches,
                        bottom_branches
                    )
                    
                    st.session_state["infographic_bytes"] = img_bytes
                    st.session_state["infographic_filename"] = f"Performance_Infographic_{selected_inf_metric}_{selected_inf_basis.split()[0]}_{selected_inf_date}.png"
        
        if "infographic_bytes" in st.session_state:
            st.success("🎉 Infographic generated successfully!")
            
            # Show download button
            st.download_button(
                label="📥 Download High-Resolution Infographic (PNG)",
                data=st.session_state["infographic_bytes"],
                file_name=st.session_state["infographic_filename"],
                mime="image/png",
                use_container_width=True
            )
            
            # Show a beautiful live preview of the infographic in Streamlit
            st.markdown("### 🖼️ Infographic Live Preview")
            st.image(st.session_state["infographic_bytes"], use_container_width=True)

    # Full Data View
    with st.expander("📋 Detailed MIS Inventory"):
        render_data_table(frame, "Complete Snapshot", f"mis_snapshot_{snapshot.selected_date}.xlsx")
