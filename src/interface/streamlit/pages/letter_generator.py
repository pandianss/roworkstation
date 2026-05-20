from __future__ import annotations
import streamlit as st
import datetime
import pandas as pd
from src.application.services.performance_letter_service import PerformanceLetterService
from src.application.services.master_service import MasterService
from src.application.use_cases.mis.service import MISAnalyticsService
from src.interface.streamlit.components.primitives import render_action_bar

def render() -> None:
    letter_service = PerformanceLetterService()
    analytics_service = MISAnalyticsService()
    master_service = MasterService()
    
    render_action_bar("Letter Generator", ["Budget Communication", "Performance Appreciation", "Shortfall Explanations"])
    
    # Fetch distinct available dates from database metadata
    dates = analytics_service.get_available_dates()
    if not dates:
        st.error("No MIS data found. Please upload MIS files in the Business Analytics page.")
        return

    tabs = st.tabs(["📬 Performance Letters", "🎯 Budget Communication", "📜 Custom Correspondence", "🎖️ Appreciation Certificates"])
    
    with tabs[0]:
        # ... (keep existing performance letters logic)
        render_performance_letters_tab(letter_service, dates, master_service)

    with tabs[1]:
        # ... (keep existing budget communication logic)
        render_budget_communication_tab(letter_service, master_service)

    with tabs[2]:
        st.markdown("### 📜 Custom Regional Correspondence")
        st.caption("Tools for drafting internal notes, bulk outreach, and ad-hoc professional letters.")
        
        sub_tabs = st.tabs(["📝 Internal (Office Note)", "📧 External (Mail Merge)", "📄 Single Ad-hoc Letter"])
        
        with sub_tabs[0]:
            from src.interface.streamlit.pages.execution import render_office_note_tab
            from src.application.services.document import DocumentService
            render_office_note_tab(DocumentService(), MasterService)
            
        with sub_tabs[1]:
            from src.interface.streamlit.pages.execution import render_mail_merge_tab
            from src.application.services.mail_merge_service import MailMergeService
            render_mail_merge_tab(MailMergeService())
            
        with sub_tabs[2]:
            st.subheader("Ad-hoc Professional Letter")
            st.info("Draft a single professional letter on official bank letterhead with trilingual header and signature.")
            
            with st.form("adhoc_letter_form"):
                col1, col2 = st.columns(2)
                with col1:
                    recipient_name = st.text_input("Recipient Name", placeholder="e.g. The Branch Manager / Customer Name")
                    subject = st.text_input("Subject")
                with col2:
                    ref_no = st.text_input("Reference No (Optional)", placeholder="e.g. RO/DGL/GEN/2026/01")
                    letter_date = st.date_input("Letter Date", value=datetime.date.today())
                
                recipient_address = st.text_area("Recipient Address", placeholder="e.g. Main Branch, Dindigul - 624001")
                
                body = st.text_area("Letter Body", height=250, placeholder="Type the content of your letter here...")
                
                use_html = st.checkbox("Enable HTML in Body", value=False)
                
                exec_list = master_service.get_ro_executives()
                exec_options = {e["roll"]: e["name"] for e in exec_list}
                sig_roll = st.selectbox("Signing Authority (External)", options=list(exec_options.keys()), format_func=lambda x: exec_options[x], key="adhoc_sig")
                
                if st.form_submit_button("Generate Professional Letter"):
                    if not recipient_name or not subject or not body:
                        st.error("Please fill in the required fields (Recipient, Subject, Body).")
                    else:
                        with st.spinner("Generating PDF..."):
                            doc_service = DocumentService()
                            pdf_bytes = doc_service.generate_custom_letter_pdf(
                                recipient_name=recipient_name,
                                recipient_address=recipient_address,
                                subject=subject,
                                body=body,
                                signatory_roll=sig_roll,
                                ref_no=ref_no if ref_no else None,
                                date=letter_date.strftime("%d.%m.%Y"),
                                is_html=use_html
                            )
                            st.session_state["adhoc_pdf"] = pdf_bytes
                            st.session_state["adhoc_filename"] = f"Letter_{recipient_name.replace(' ', '_')}.pdf"
            
            if "adhoc_pdf" in st.session_state:
                st.download_button(
                    label="📥 Download Professional Letter",
                    data=st.session_state["adhoc_pdf"],
                    file_name=st.session_state["adhoc_filename"],
                    mime="application/pdf",
                    use_container_width=True
                )

    with tabs[3]:
        st.markdown("### 🎖️ Appreciation Certificate")
        st.caption("Generate a formal appreciation certificate for staff members for specific contributions.")
        
        with st.form("cert_generator_form"):
            col1, col2 = st.columns(2)
            with col1:
                recip_roll = st.text_input("Staff Roll Number", placeholder="e.g. 36614")
            
            # Resolve name for preview
            staff_df = master_service.get_staff_frame()
            match = staff_df[staff_df['Roll No'] == recip_roll.strip()] if recip_roll.strip() else pd.DataFrame()
            
            if not match.empty:
                st.success(f"Recipient: **{match.iloc[0]['Name (En)']}** ({match.iloc[0]['Designation']})")
            elif recip_roll.strip():
                st.warning("Staff Roll Number not found in registry.")

            with col2:
                cert_date = st.date_input("Certificate Date", value=datetime.date.today())
            
            reason = st.text_area("Reason for Appreciation", placeholder="e.g. exceptional support in recovery of NPA accounts / proactive customer service during the mega camp")
            
            exec_list = master_service.get_ro_executives()
            exec_options = {e["roll"]: e["name"] for e in exec_list}
            cert_sig_roll = st.selectbox("Signing Authority (Certificate)", options=list(exec_options.keys()), format_func=lambda x: exec_options[x], key="cert_sig")
            
            if st.form_submit_button("🎖️ Generate Certificate"):
                if not recip_roll or not reason:
                    st.error("Please provide both Roll Number and Reason.")
                elif match.empty:
                    st.error("Cannot generate certificate for unknown roll number.")
                else:
                    with st.spinner("Generating Certificate..."):
                        from src.application.services.document import DocumentService
                        doc_service = DocumentService()
                        pdf_bytes = doc_service.generate_appreciation_certificate_pdf(
                            recipient_roll=recip_roll.strip(),
                            reason=reason,
                            signatory_roll=cert_sig_roll,
                            date=cert_date.strftime("%d.%m.%Y")
                        )
                        st.session_state["cert_pdf"] = pdf_bytes
                        st.session_state["cert_filename"] = f"Certificate_{recip_roll}_{datetime.date.today().strftime('%Y%m%d')}.pdf"

        if "cert_pdf" in st.session_state:
            st.divider()
            st.download_button(
                label="📥 Download Appreciation Certificate",
                data=st.session_state["cert_pdf"],
                file_name=st.session_state["cert_filename"],
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )

def render_performance_letters_tab(letter_service, dates, master_service):
    st.markdown("### 📈 Monthly Performance Communication")
    st.caption("Generate mass appreciation and explanation letters based on budget performance.")
    
    # Date and Month selection
    col_m, col_s = st.columns([2, 2])
    
    # Group available dates by Month-Year for selection
    month_options = {}
    for d in reversed(dates):
        m_key = d.strftime("%B %Y")
        if m_key not in month_options:
            month_options[m_key] = d # Keep the latest date for that month
    
    selected_perf_month_key = col_m.selectbox("Target Month", options=list(month_options.keys()), key="lg_perf_month")
    perf_date = month_options[selected_perf_month_key]
    
    # Signatory selection
    exec_list = master_service.get_ro_executives()
    exec_options = {e["roll"]: e["name"] for e in exec_list}
    selected_sig_roll = col_s.selectbox("Signing Authority", options=list(exec_options.keys()), format_func=lambda x: exec_options[x], key="lg_perf_sig")
    selected_signatory = next((e for e in exec_list if e["roll"] == selected_sig_roll), None)

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

        if st.button("📦 Generate All Performance Letters (ZIP)", use_container_width=True, type="primary"):
            if not selected_signatory: 
                st.error("Please select a signatory.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress_perf(pct, msg):
                    progress_bar.progress(pct)
                    status_text.text(msg)
                
                zip_data = letter_service.generate_letters_zip(
                    performance_data, 
                    signatory=selected_signatory,
                    progress_callback=update_progress_perf
                )
                
                progress_bar.empty()
                status_text.empty()
                st.success(f"Generated performance letters for {len(performance_data)} branches!")
                st.download_button("📥 Download Performance Kit", data=zip_data, file_name=f"Performance_Letters_{perf_date}.zip", mime="application/zip", use_container_width=True)
    else:
        st.info(f"No performance data available for {perf_date}.")

def render_budget_communication_tab(letter_service, master_service):
    st.markdown("### 🎯 Annual Budget Communication")
    status = letter_service.budget_repo.get_sync_status()
    st.caption(f"🛡️ **Data Maintenance:** Last synced on {status['last_sync']} | FYs available: {', '.join(status['fy_ranges'])}")
    
    st.info("Generate formal budget communication letters for all parameters defined in the registry.")
    
    # FY & Communication Date
    fcol1, fcol2 = st.columns(2)
    selected_fy = fcol1.selectbox("Target Fiscal Year", options=status["fy_ranges"], index=len(status["fy_ranges"])-1 if status["fy_ranges"] else 0, key="lg_budget_fy")
    comm_date = fcol2.date_input("Date of Communication", value=datetime.date.today(), key="lg_budget_comm_date")
    
    # Signatory selection for budget
    exec_list = master_service.get_ro_executives()
    exec_options = {e["roll"]: e["name"] for e in exec_list}
    selected_sig_roll_budget = st.selectbox("Signing Authority (Budget)", options=list(exec_options.keys()), format_func=lambda x: exec_options[x], key="lg_budget_sig")
    
    # Convert selected_fy (e.g. "2026-27") to a date for target retrieval
    try:
        fy_start_year = int(selected_fy.split("-")[0])
        fy_ref_date = datetime.date(fy_start_year, 4, 1)
    except:
        fy_ref_date = datetime.date.today()

    if st.button("🚀 Generate Budget Letters (ZIP)", use_container_width=True, type="primary"):
        budget_data = letter_service.get_budget_communication_data(fy_ref_date)
        if not budget_data:
            st.error(f"No budget data found for {selected_fy}.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress_budget(pct, msg):
                progress_bar.progress(pct)
                status_text.text(msg)
            
            signatory_profile = letter_service.doc_service._resolve_staff_profile(selected_sig_roll_budget)
            formatted_comm_date = comm_date.strftime("%d.%m.%Y")
            zip_bytes = letter_service.generate_budget_zip(
                budget_data, 
                signatory_profile, 
                progress_callback=update_progress_budget,
                comm_date=formatted_comm_date
            )
            
            progress_bar.empty()
            status_text.empty()
            if zip_bytes:
                st.success(f"Generated budget letters for {len(budget_data)} branches!")
                st.download_button("📥 Download Budget Letters ZIP", data=zip_bytes, file_name=f"Budget_Communication_{selected_fy}.zip", mime="application/zip", use_container_width=True)
