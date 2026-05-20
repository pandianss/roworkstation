from __future__ import annotations

import datetime
import streamlit as st
from src.application.services.returns_service import ReturnsService
from src.interface.streamlit.components.primitives import render_action_bar, render_data_table, render_filter_panel

@st.cache_resource
def get_service():
    return ReturnsService()

def render() -> None:
    service = get_service()
    
    render_action_bar("Statutory & Periodic Returns", ["Compliance Tracking", "Compliance Log"])
    render_filter_panel("Control Tower", "Manage and monitor regional statutory reporting obligations.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Create Requirement")
        with st.form("new_return_form", clear_on_submit=True):
            title = st.text_input("Return Title", placeholder="e.g. Weekly Cash Position")
            freq = st.selectbox("Frequency", ["Weekly", "Fortnightly", "Monthly", "Quarterly", "Half-Yearly", "Yearly"])
            due = st.date_input("Next Due Date", value=datetime.date.today() + datetime.timedelta(days=7))
            dept = st.text_input("Owner Department", value=st.session_state.get("user_dept", "PLAN"))
            
            if st.form_submit_button("Add Return Requirement", use_container_width=True):
                if title:
                    service.create_return(title, freq, due, dept)
                    st.success(f"Requirement '{title}' created.")
                    st.rerun()
                else:
                    st.error("Title is required.")

    with col2:
        st.markdown("### Active Tracking")
        df = service.get_as_frame()
        if not df.empty:
            # Add status coloring logic if possible via primitives, or just render table
            render_data_table(df, "Regional Compliance Log", "statutory_returns.xlsx")
            
            st.markdown("---")
            st.markdown("### Quick Actions")
            pending = [r for r in service.get_all() if r["status"] == "Pending"]
            if pending:
                selected_ret = st.selectbox("Mark as Completed", options=[r["id"] for r in pending], format_func=lambda x: next(r["title"] for r in pending if r["id"] == x))
                if st.button("Confirm Completion"):
                    service.update_status(selected_ret, "Completed")
                    st.success("Status updated.")
                    st.rerun()
            else:
                st.info("No pending returns to update.")
        else:
            st.info("No return requirements configured.")

    st.divider()
    st.caption("Note: This section is visible to Regional Office (RO) and Admin users only.")
