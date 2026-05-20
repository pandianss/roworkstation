from __future__ import annotations

import datetime
import html
import pandas as pd
import streamlit as st

from src.application.services.circular_service import CircularService
from src.interface.streamlit.state.services import (
    get_doc_service_v4, get_task_service, get_circular_service, 
    get_mm_service, get_master_service
)
from src.interface.streamlit.components.primitives import render_action_bar, render_chart_container, render_data_table

def prepare_content(text: str, use_html: bool) -> str:
    """Safely prepares text for rendering in HTML templates."""
    if not use_html:
        # Escape any accidental HTML tags and return as-is (template handles pre-wrap)
        return html.escape(text)
    return text

def render() -> None:
    task_service = get_task_service()
    doc_service = get_doc_service_v4()
    mm_service = get_mm_service()
    circ_service = get_circular_service()

    render_action_bar("Document Center & Execution", ["Circulars", "Office Notes", "Mail Merge", "Tasks"])
    
    tabs = st.tabs(["📜 Official Circulars", "📝 Office Note Generator", "📬 Bulk Mail Merge", "📊 Task Analytics"])
    
    with tabs[0]:
        render_circular_management_tab(circ_service, doc_service)
    
    with tabs[1]:
        render_office_note_tab(doc_service, get_master_service)
        
    with tabs[2]:
        render_mail_merge_tab(mm_service)
        
    with tabs[3]:
        render_task_analytics_tab(task_service)

def render_circular_management_tab(circ_service, doc_service):
    st.subheader("Official Circular Management")
    st.info("Draft and manage regional circulars with auto-incrementing reference numbers.")
    
    master_svc = get_master_service()
    dept_records = master_svc.get_by_category("DEPT")
    dept_map = {d.code: f"{d.code} - {d.name_en}" for d in dept_records}
    dept_map["ALL"] = "ALL - All Departments"
    dept_options = ["ALL"] + sorted([d.code for d in dept_records])
    default_dept = st.session_state.get("user_dept", "PLAN")
    if default_dept not in dept_options:
        default_dept = "ALL"
    
    with st.form("circular_form"):
        c1, c2 = st.columns(2)
        with c1:
            circ_dept = st.selectbox("Department Code", options=dept_options, index=dept_options.index(default_dept), format_func=lambda x: dept_map.get(x, x))
            circ_subject = st.text_input("Circular Subject")
        with c2:
            region_code = "DGL" # Default for Dindigul
            ref_no = circ_service.generate_ref_no(region_code, circ_dept)
            st.text_input("Reference Number", value=ref_no, disabled=True)
            issuance_date = st.date_input("Issuance Date", value=datetime.date.today())
        
        recipients = st.radio("Recipients", ["All Branches", "Specific Selection"], horizontal=True)
        circ_body = st.text_area("Circular Body Content", height=300, help="Use <b>, <i>, <ul>, <li> tags if HTML is enabled.")
        circ_conclusion = st.text_input("Conclusion / Instructions", value="Please acknowledge receipt and ensure compliance.")
        
        use_html_circ = st.checkbox("Enable HTML Formatting", value=False, help="Interpret body and conclusion as HTML.")
        circ_submitted = st.form_submit_button("Save Circular Draft")
        
        if circ_submitted:
            circular = {
                "ref_no": ref_no,
                "subject": circ_subject,
                "dept": circ_dept,
                "date": issuance_date.isoformat(),
                "recipients": recipients,
                "body": prepare_content(circ_body, use_html_circ),
                "conclusion": prepare_content(circ_conclusion, use_html_circ),
                "author": st.session_state.get("username", "Staff"),
                "is_html": use_html_circ
            }
            circ_service.save_circular(circular)
            st.success(f"Circular {ref_no} saved successfully!")

    st.markdown("#### Recent Circulars")
    all_circs = circ_service.get_all()
    if all_circs:
        for i, c in enumerate(all_circs):
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1])
                with col_info:
                    is_new = False
                    try:
                        c_date_str = c.get('date', '')
                        p_date = datetime.datetime.fromisoformat(c_date_str) if 'T' in c_date_str else datetime.datetime.strptime(c_date_str, "%Y-%m-%d")
                        if (datetime.datetime.now() - p_date).days <= 7:
                            is_new = True
                    except (TypeError, ValueError):
                        pass
                    
                    # Unified date formatting
                    date_val = c.get('date', '')
                    try:
                        p_date = datetime.datetime.fromisoformat(date_val) if 'T' in date_val else datetime.datetime.strptime(date_val, "%Y-%m-%d")
                        fmt_date = p_date.strftime("%d.%m.%Y")
                    except: fmt_date = date_val

                    subject = c.get('subject', 'No Subject')
                    ref = c.get('ref_no', 'No Ref')
                    st.markdown(f"### {'🆕 ' if is_new else ''}{subject}")
                    st.markdown(f"**Ref:** `{ref}` | **Date:** {fmt_date} | **Author:** {c.get('author', 'Regional Office')}")
                
                with col_action:
                    st.write("") 
                    circ_id = f"circ_{i}_{ref.replace('/', '_')}"
                    if st.button("📄 Prepare", key=f"prep_{circ_id}", use_container_width=True):
                        with st.spinner("Generating..."):
                            pdf_bytes = doc_service.generate_circular_pdf(c)
                            st.session_state[f"pdf_{circ_id}"] = pdf_bytes
                    
                    if f"pdf_{circ_id}" in st.session_state:
                        st.download_button(
                            "📥 Download",
                            data=st.session_state[f"pdf_{circ_id}"],
                            file_name=f"Circular_{ref.replace('/', '_')}.pdf",
                            mime="application/pdf",
                            key=f"dl_{circ_id}",
                            use_container_width=True
                        )
    else:
        st.info("No published circulars found.")

def render_office_note_tab(doc_service, get_master_service):
    st.subheader("Trilingual Office Note Generator")
    st.info("Generates notes with standard trilingual headers. You can use HTML for advanced formatting.")
    
    master_svc = get_master_service()
    dept_records = master_svc.get_by_category("DEPT")
    dept_map = {d.code: f"{d.code} - {d.name_en}" for d in dept_records}
    dept_options = sorted([d.code for d in dept_records])
    default_dept = st.session_state.get("user_dept", "PLAN")
    if default_dept not in dept_options:
        default_dept = dept_options[0] if dept_options else "PLAN"
        
    with st.form("office_note_form"):
        col1, col2 = st.columns(2)
        with col1:
            dept = st.selectbox("Department", options=dept_options, index=dept_options.index(default_dept) if dept_options else 0, format_func=lambda x: dept_map.get(x, x))
        with col2:
            ref = st.text_input("Reference No (Optional)")
            
        subject = st.text_input("Subject")
        prepared_by = st.session_state.get("display_name") or st.session_state.get("username", "Staff User")
        
        exec_list = get_master_service().get_ro_executives()
        exec_options = {e["roll"]: e["name"] for e in exec_list}
        selected_sig_rolls = st.multiselect("Signing Authorities (Scale IV & Above)", options=list(exec_options.keys()), format_func=lambda x: exec_options[x], help="Select one or more executives to sign the office note.")
        signatories = selected_sig_rolls
        
        intro = st.text_area("Introduction / Context", height=100)
        obs = st.text_area("Observations / Technical Details", height=150)
        recs = st.text_area("Recommendations / Action Points", height=100)
        
        use_html_note = st.checkbox("Enable HTML Formatting", value=False, help="Use tags like <b>, <ul>, <li> to format your content.")
        
        if st.form_submit_button("Generate Trilingual Note"):
            if not subject or not intro or not recs:
                st.error("Please fill in the required fields.")
            else:
                html_content = {
                    "intro": prepare_content(intro, use_html_note),
                    "obs": prepare_content(obs, use_html_note),
                    "recs": prepare_content(recs, use_html_note)
                }
                html_doc = doc_service.generate_office_note(
                    department=dept, 
                    subject=subject, 
                    intro_text=html_content["intro"], 
                    observations=html_content["obs"], 
                    recommendations=html_content["recs"], 
                    prepared_by=prepared_by, 
                    ref_no=ref or None, 
                    signatories=signatories,
                    is_html=use_html_note
                )
                st.session_state["preview_note"] = html_doc
                st.session_state["note_params"] = {
                    "dept": dept, "subject": subject, "intro": html_content["intro"], 
                    "obs": html_content["obs"], "recs": html_content["recs"], 
                    "prep": prepared_by, "ref": ref, "sigs": signatories,
                    "is_html": use_html_note
                }
    
    if "preview_note" in st.session_state:
        st.markdown("### Preview")
        st.components.v1.html(st.session_state["preview_note"], height=500, scrolling=True)
        col_h, col_p, col_s = st.columns(3)
        params = st.session_state["note_params"]
        with col_h:
            st.download_button("Download HTML", data=st.session_state["preview_note"], file_name="Office_Note.html", mime="text/html", use_container_width=True)
        with col_p:
            pdf_data = doc_service.generate_pdf_note(
                department=params["dept"], 
                subject=params["subject"], 
                intro_text=params["intro"], 
                observations=params["obs"], 
                recommendations=params["recs"], 
                prepared_by=params["prep"], 
                ref_no=params["ref"] or None, 
                signatories=params["sigs"],
                is_html=params["is_html"]
            )
            st.download_button("Download PDF (Official)", data=pdf_data, file_name="Office_Note.pdf", mime="application/pdf", use_container_width=True)
        
        with col_s:
            from src.application.services.document.office_note_service import OfficeNoteService
            if st.button("💾 Save to Repository", use_container_width=True, type="primary"):
                note_service = OfficeNoteService()
                # Determine next ref if not provided
                final_ref = params["ref"]
                if not final_ref:
                    final_ref = note_service.generate_next_reference(params["dept"])
                
                new_note = {
                    "type": "CUSTOM",
                    "status": "DRAFT",
                    "titleEn": params["subject"],
                    "referenceNo": final_ref,
                    "parsed_content": {
                        "deptName": params["dept"],
                        "details": f"<h3>Introduction</h3>{params['intro']}<h3>Observations</h3>{params['obs']}<h3>Recommendations</h3>{params['recs']}",
                        "intro": params["intro"],
                        "obs": params["obs"],
                        "recs": params["recs"],
                        "signatorySnapshot": {
                            "preparer": {"name": params["prep"]},
                            "reviewers": [{"name": s} for s in params["sigs"]]
                        },
                        "noteDate": datetime.date.today().isoformat()
                    }
                }
                note_service.save_note(new_note)
                st.success(f"Note saved with Ref: {final_ref}")

        st.divider()
        st.subheader("Branch Anniversary Note")
        with st.form("anniversary_note_form"):
            col1, col2 = st.columns(2)
            with col1:
                br_name = st.text_input("Branch Name")
                br_code = st.text_input("Branch SOL Code")
            with col2:
                f_date = st.text_input("Foundation Date")
                years = st.number_input("Anniversary Year", min_value=1, value=50)
            if st.form_submit_button("Generate Anniversary Note"):
                html_anniv = doc_service.generate_anniversary_note(branch_name=br_name, branch_code=br_code, foundation_date=f_date, years=int(years), prepared_by=st.session_state.get("username", "Staff User"))
                st.session_state["preview_note_anniv"] = html_anniv
        if "preview_note_anniv" in st.session_state:
            st.components.v1.html(st.session_state["preview_note_anniv"], height=400, scrolling=True)

def render_mail_merge_tab(mm_service):
    st.subheader("Bulk Mail Merge Engine")
    st.info("Upload an Excel file with columns matching your template variables (e.g., {{NAME}}, {{ADDRESS}}).")
    col_t, col_d = st.columns(2)
    with col_t:
        st.markdown("#### 1. Define HTML Template")
        template_text = st.text_area("HTML Content", value="""<div style="font-family: Arial; padding: 40px;"><h1>Notice to {{NAME}}</h1><p>Dear {{NAME}},</p><p>This is regarding your account with SOL <strong>{{BRANCH}}</strong>.</p><br><p>Regional Manager,<br>Dindigul</p></div>""", height=300)
    with col_d:
        st.markdown("#### 2. Upload Data Source")
        data_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"], key="mm_file_exec")
        if data_file:
            df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
            st.dataframe(df.head(), use_container_width=True)
            if st.button("🚀 Process Bulk Merge"):
                with st.spinner("Processing..."):
                    try:
                        zip_bytes = mm_service.process_merge_zip(template_text, df)
                        st.download_button("Download All (Zipped)", data=zip_bytes, file_name="merged_documents.zip", mime="application/zip", use_container_width=True)
                    except Exception as e:
                        st.error(f"Merge failed: {str(e)}")

def render_task_analytics_tab(task_service):
    st.subheader("Regional Workload Analytics")
    tasks = task_service.as_frame(st.session_state.get("username", ""))
    if tasks.empty:
        st.info("No task data.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            status_counts = tasks["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            render_chart_container(status_counts, "status", "count", "Task Status", kind="pie")
        with col2:
            priority_counts = tasks["priority"].value_counts().reset_index()
            priority_counts.columns = ["priority", "count"]
            render_chart_container(priority_counts, "priority", "count", "Priority", kind="bar", color="priority")
        render_data_table(tasks, "Task Inventory", "task_inventory.xlsx")
