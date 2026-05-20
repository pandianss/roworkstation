from __future__ import annotations

import datetime
import streamlit as st
import pandas as pd
from src.interface.streamlit.components.primitives import (
    render_action_bar, render_premium_metrics, render_data_table, render_section_divider, render_info_banner
)
from src.application.services.account_performance_service import AccountPerformanceService

def render() -> None:
    render_action_bar(
        "Account Opening Performance Portal",
        ["Working Days Concept", "SB Daily Run Rate", "CD Monthly Run Rate"]
    )

    service = AccountPerformanceService()

    tab_parameters, tab_calendar, tab_ingestion = st.tabs([
        "⚙️ Thresholds & Date Filters",
        "📅 Holiday Calendar",
        "📥 Data Ingestion"
    ])

    with tab_ingestion:
        st.markdown("### 📥 Ingest Operational Data feeds")
        st.caption("Upload daily or monthly export feeds for account openings and closures to compile regional run rates.")
        
        col1, col2 = st.columns(2)
        with col1:
            open_file = st.file_uploader(
                "Upload Accounts Opened Feed (Open.csv)",
                type=["csv"],
                key="open_uploader",
                help="CSV must contain: SOL_ID, ACCT_OPN_DATE, SCHM_TYPE (SBA/CAA), CLR_BAL_AMT, AVERAGE BALANCE"
            )
        with col2:
            close_file = st.file_uploader(
                "Upload Accounts Closed Feed (Closure (1).csv)",
                type=["csv"],
                key="close_uploader",
                help="CSV must contain: SOL_ID, ACCT_CLS_DATE, SCHM_TYPE (SBA/CAA)"
            )

        if open_file:
            try:
                stats = service.import_openings_csv(open_file.read())
                st.success(f"🎉 Successfully ingested {stats['count']} openings records across {len(stats['dates'])} dates!")
            except Exception as e:
                st.error(f"Failed to ingest openings feed: {e}")

        if close_file:
            try:
                stats = service.import_closures_csv(close_file.read())
                st.success(f"🎉 Successfully ingested {stats['count']} closure records across {len(stats['dates'])} dates!")
            except Exception as e:
                st.error(f"Failed to ingest closures feed: {e}")

    with tab_calendar:
        st.markdown("### 📅 Comprehensive Calendar & Holidays")
        st.caption("Add public holidays to exclude them from the SB Daily Run Rate working days calculation.")
        
        st.markdown("#### Add Public Holiday")
        c1, c2, c3 = st.columns([2, 3, 1])
        with c1:
            h_date = st.date_input("Holiday Date", value=datetime.date.today(), key="new_holiday_date")
        with c2:
            h_name = st.text_input("Holiday Description", value="Public Holiday", key="new_holiday_name")
        with c3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Add Holiday", use_container_width=True):
                service.add_public_holiday(h_date, h_name)
                st.success(f"Added holiday: {h_name} on {h_date}")
                st.rerun()

        st.markdown("#### Active Public Holidays List")
        holidays = service.get_public_holidays()
        if holidays:
            for h in holidays:
                col_h_info, col_h_del = st.columns([5, 1])
                with col_h_info:
                    st.markdown(f"🗓️ **{datetime.datetime.strptime(h['date'], '%Y-%m-%d').strftime('%d.%m.%Y')}** — {h['name']}")
                with col_h_del:
                    if st.button("Delete", key=f"del_{h['date']}", use_container_width=True):
                        service.delete_public_holiday(h['date'])
                        st.rerun()
        else:
            st.info("No public holidays configured. Only Sundays and Saturdays (if enabled) are marked as holidays.")

    with tab_parameters:
        min_date, max_date = service.get_date_limits()
        if not min_date or not max_date:
            render_info_banner(
                "No Data Ingested Yet",
                "Please upload the required CSV feeds (Open.csv and Closure (1).csv) in the 'Data Ingestion' tab first.",
                icon="⚠️"
            )
            return

        st.markdown("### ⚙️ Thresholds & Filters Settings")
        
        c_date, c_opts = st.columns([2, 1])
        with c_date:
            selected_range = st.date_input(
                "Performance Period Filter",
                value=(min_date, max_date),
                help="Filter account openings and closures within this range."
            )
        with c_opts:
            threshold_field = st.selectbox(
                "Validation Balance Metric",
                options=["clr_bal_amt", "average_balance"],
                format_func=lambda x: "Clear Balance (CLR_BAL_AMT)" if x == "clr_bal_amt" else "Average Balance",
                help="Balance field to evaluate against quality threshold."
            )

        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start_dt, end_dt = selected_range
        elif isinstance(selected_range, list) and len(selected_range) == 2:
            start_dt, end_dt = selected_range[0], selected_range[1]
        else:
            start_dt = selected_range
            end_dt = selected_range

        st.markdown("#### 🌾 Savings Bank (SBA) Quality Thresholds")
        col_sba_r, col_sba_su, col_sba_u, col_sba_m = st.columns(4)
        with col_sba_r:
            sba_r = st.number_input("Rural Threshold (₹)", min_value=0.0, value=1000.0, step=100.0)
        with col_sba_su:
            sba_su = st.number_input("Semi-Urban Threshold (₹)", min_value=0.0, value=1000.0, step=100.0)
        with col_sba_u:
            sba_u = st.number_input("Urban Threshold (₹)", min_value=0.0, value=1000.0, step=100.0)
        with col_sba_m:
            sba_m = st.number_input("Metropolitan Threshold (₹)", min_value=0.0, value=1000.0, step=100.0)

        st.markdown("#### 🏢 Current Account (CD/CAA) Quality Thresholds")
        col_caa_r, col_caa_su, col_caa_u, col_caa_m = st.columns(4)
        with col_caa_r:
            caa_r = st.number_input("Rural Threshold (₹) ", min_value=0.0, value=5000.0, step=500.0)
        with col_caa_su:
            caa_su = st.number_input("Semi-Urban Threshold (₹) ", min_value=0.0, value=10000.0, step=500.0)
        with col_caa_u:
            caa_u = st.number_input("Urban Threshold (₹) ", min_value=0.0, value=10000.0, step=500.0)
        with col_caa_m:
            caa_m = st.number_input("Metropolitan Threshold (₹) ", min_value=0.0, value=10000.0, step=500.0)

        exclude_sat = st.checkbox(
            "Exclude 2nd & 4th Saturdays from Banking Days",
            value=True,
            help="Exclude standard Indian banking Saturday holidays."
        )

        perf_data = service.get_performance_data(
            start_date=start_dt,
            end_date=end_dt,
            sba_thresholds={
                "RURAL": sba_r,
                "SEMI URBAN": sba_su,
                "URBAN": sba_u,
                "METROPOLITAN": sba_m
            },
            caa_thresholds={
                "RURAL": caa_r,
                "SEMI URBAN": caa_su,
                "URBAN": caa_u,
                "METROPOLITAN": caa_m
            },
            threshold_field=threshold_field,
            exclude_2nd_4th_sat=exclude_sat
        )
        summary = perf_data["summary"]

        render_section_divider()

        # Metrics Display
        st.markdown("#### 📈 Regional Performance Overview")
        col_sb, col_cd = st.columns(2)
        
        with col_sb:
            st.markdown("""
                <div style="background: rgba(30, 41, 59, 0.4); padding: 12px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 12px;">
                    <strong style="color: #60a5fa;">Savings Bank (SB) Performance Indicators</strong>
                </div>
            """, unsafe_allow_html=True)
            render_premium_metrics({
                "SBA Opened": summary["sba_opened"],
                "SBA Low Balance": summary["sba_low_bal"],
                "SBA Closed": summary["sba_closed"],
                "Net SBA": summary["sba_net"],
                "SB Working Days": summary["working_days"],
                "SB Daily Run Rate": round(summary["sba_run_rate"], 2)
            })

        with col_cd:
            st.markdown("""
                <div style="background: rgba(30, 41, 59, 0.4); padding: 12px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 12px;">
                    <strong style="color: #34d399;">Current Account (CD) Performance Indicators</strong>
                </div>
            """, unsafe_allow_html=True)
            render_premium_metrics({
                "CAA Opened": summary["caa_opened"],
                "CAA Low Balance": summary["caa_low_bal"],
                "CAA Closed": summary["caa_closed"],
                "Net CAA": summary["caa_net"],
                "Monitoring Months": round(summary["months"], 2),
                "CD Monthly Run Rate": round(summary["caa_run_rate"], 2)
            })

        render_section_divider()

        # Branch-wise Performance Grid
        st.markdown("#### 🏢 Branch-wise Account Performance Details")
        st.caption("Detailed branch-level performance breakdown showing branch type, openings, deductions, net count, and run rates.")

        branches_df = pd.DataFrame(perf_data["branches"])
        if not branches_df.empty:
            branches_df.rename(
                columns={
                    "sol": "SOL ID",
                    "name": "Branch Name",
                    "type": "Branch Type",
                    "sba_opened": "SBA Opened",
                    "sba_low_bal": "SBA Low Bal",
                    "sba_closed": "SBA Closed",
                    "sba_net": "Net SBA",
                    "sba_run_rate": "SBA Daily Run Rate",
                    "caa_opened": "CAA Opened",
                    "caa_low_bal": "CAA Low Bal",
                    "caa_closed": "CAA Closed",
                    "caa_net": "Net CAA",
                    "caa_run_rate": "CAA Monthly Run Rate"
                },
                inplace=True
            )
            
            branches_df["SBA Daily Run Rate"] = branches_df["SBA Daily Run Rate"].round(2)
            branches_df["CAA Monthly Run Rate"] = branches_df["CAA Monthly Run Rate"].round(2)

            render_data_table(
                branches_df,
                "Branch Performance Standings",
                f"Account_Opening_Performance_{start_dt}_to_{end_dt}.xlsx"
            )
        else:
            st.info("No branch record matched the selected filters.")
