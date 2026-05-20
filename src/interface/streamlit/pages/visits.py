from __future__ import annotations

import datetime
import io
import zipfile
import streamlit as st
import pandas as pd

from src.application.services.visit_service import VisitService
from src.application.services.document import DocumentService
from src.interface.streamlit.components.primitives import render_action_bar, render_data_table
from src.infrastructure.persistence.master_repository import MasterRepository
from src.interface.streamlit.state.services import get_master_service

def render() -> None:
    render_action_bar("Region Head Branch Visits", ["Visit Tracking", "Monthly Returns", "Observation Letters"])

    service = VisitService()
    doc_service = DocumentService()
    
    # 1. Period Selection
    now = datetime.date.today()
    col_m, col_y = st.columns(2)
    with col_m:
        month = st.selectbox("Select Month", range(1, 13), index=now.month - 1, format_func=lambda x: datetime.date(2026, x, 1).strftime("%B"))
    with col_y:
        year = st.selectbox("Select Year", range(2024, 2028), index=range(2024, 2028).index(now.year))

    st.divider()

    # 2. Wizard Tabs
    tab1, tab2 = st.tabs(["📝 Record New Visit", "📊 Monthly Return & Letters"])

    with tab1:
        st.markdown("### Log Executive Branch Visit")
        with st.form("visit_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            # Fetch Branches for dropdown
            repo = MasterRepository()
            branches = repo.get_by_category("UNIT")
            branch_options = sorted([int(b.code) for b in branches if b.code.isdigit()])
            branch_map = {int(b.code): f"{b.code} - {b.name_en}" for b in branches if b.code.isdigit()}

            with col1:
                sol = st.selectbox("Branch SOL", options=branch_options, format_func=lambda x: branch_map.get(x, f"SOL {x}"))
                visit_date = st.date_input("Date of Visit", value=now)
            with col2:
                visitor = st.text_input("Visiting Executive Name", placeholder="e.g. SRM / CRM / RM")
            
            observations = st.text_area("Major Observations", placeholder="Enter key irregularities or performance notes...")
            advice = st.text_area("Advice / Directions given to Branch", placeholder="Enter rectification instructions...")
            
            if st.form_submit_button("Save Visit Record", use_container_width=True):
                if sol and visitor and observations:
                    service.add_visit(sol, visit_date, visitor, observations, advice)
                    st.success(f"Visit to SOL {sol} recorded successfully!")
                else:
                    st.error("Please fill all required fields (SOL, Visitor, Observations).")

    with tab2:
        visits = service.get_monthly_visits(year, month)
        if visits:
            st.markdown(f"### Visits for {datetime.date(year, month, 1).strftime('%B %Y')}")
            
            # Display table
            visit_data = []
            for v in visits:
                visit_data.append({
                    "ID": v.id,
                    "Date": v.visit_date.strftime("%d.%m.%Y"),
                    "SOL": v.sol,
                    "Branch": v.branch_name,
                    "Executive": v.visitor_name,
                    "Observations": v.observations[:50] + "..." if len(v.observations) > 50 else v.observations,
                    "Reply?": "✅" if v.reply_received else "⏳"
                })
            
            df = pd.DataFrame(visit_data)
            st.dataframe(df, hide_index=True, use_container_width=True)

            st.divider()
            
            # Generation Wizard
            st.markdown("### 🛠️ Document Generation Wizard")
            st.info("This will generate the Consolidated Monthly Return and individual Observation Letters for all branches listed above.")
            
            master_service = get_master_service()
            exec_list = master_service.get_ro_executives()
            exec_options = {e["roll"]: e["name"] for e in exec_list}
            
            selected_sig_roll = st.selectbox(
                "Signing Authority", 
                options=list(exec_options.keys()), 
                format_func=lambda x: exec_options[x], 
                key="visit_sig"
            )

            col_gen, col_zip = st.columns([1, 1])
            
            if col_gen.button("🚀 Prepare Return Kit", use_container_width=True):
                with st.spinner("Generating PDF documents..."):
                    # 1. Consolidated Report
                    main_pdf = doc_service.generate_branch_visit_report(month, year, visits, selected_sig_roll)
                    
                    # 2. Individual Letters
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        # Add the main report
                        zf.writestr(f"Consolidated_Visit_Return_{month}_{year}.pdf", main_pdf)
                        
                        # Add individual letters
                        for v in visits:
                            letter_pdf = doc_service.generate_visit_observation_letter(v, selected_sig_roll)
                            filename = f"Observation_Letter_{v.sol}_{v.branch_name.replace(' ', '_')}.pdf"
                            zf.writestr(f"Observation_Letters/{filename}", letter_pdf)
                    
                    st.session_state["visit_zip"] = zip_buffer.getvalue()
                    st.session_state["zip_name"] = f"Visit_Return_Kit_{month}_{year}.zip"
            
            if "visit_zip" in st.session_state:
                col_zip.download_button(
                    label="📥 Download Return Kit (ZIP)",
                    data=st.session_state["visit_zip"],
                    file_name=st.session_state["zip_name"],
                    mime="application/zip",
                    use_container_width=True
                )
            
            # Cleanup action
            if st.button("🗑️ Clear Local Records (Careful!)", help="Deletes all records for this month from the local database."):
                for v in visits:
                    service.delete_visit(v.id)
                st.warning("Month records cleared.")
                st.rerun()
        else:
            st.info(f"No visit records found for {datetime.date(year, month, 1).strftime('%B %Y')}. Use the first tab to add records.")

    st.divider()
    st.caption("Entries should be submitted by the 5th of the subsequent month as per Regional Office guidelines.")
