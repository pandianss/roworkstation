import streamlit as st
import pandas as pd
import json
import datetime
from src.core.paths import project_path
from src.interface.streamlit.components.primitives import render_action_bar, render_premium_metrics
from src.application.services.document.office_note_service import OfficeNoteService
from src.application.services.circular_service import CircularService
from src.interface.streamlit.state.services import get_doc_service_v4
from src.application.use_cases.mis.service import MISAnalyticsService

def render():
    render_action_bar("Unified Archive Hub", ["Audit Ready", "Searchable", "Centralized"])
    
    note_service = OfficeNoteService()
    circ_service = CircularService()
    mis_service = MISAnalyticsService()
    doc_service = get_doc_service_v4()
    
    # ─── REPOSITORY STATS ──────────────────────────────────────────────────
    notes_df = note_service.get_all()
    circs = circ_service.get_all()
    
    metrics = {
        "Office Notes": len(notes_df),
        "Circulars": len(circs),
        "Total Documents": len(notes_df) + len(circs),
        "Last Entry": "Today" # Placeholder
    }
    render_premium_metrics(metrics)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─── SEARCH & FILTERS ─────────────────────────────────────────────────
    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    with f_col1:
        doc_type = st.selectbox("Document Type", ["All Types", "Office Note", "Circular", "MIS Data Feed"])
    with f_col2:
        status_filter = st.selectbox("Status", ["All", "DRAFT", "FINALIZED", "PUBLISHED"])
    with f_col3:
        search_query = st.text_input("Global Search", placeholder="Search by title, ref no, or content...")

    # ─── UNIFIED DATASET ──────────────────────────────────────────────────
    unified_data = []
    
    # Process Notes
    if not notes_df.empty:
        for _, row in notes_df.iterrows():
            unified_data.append({
                "ID": row["id"],
                "Source": "Office Note",
                "Type": row["type"],
                "Title": row["titleEn"],
                "Ref No": row["referenceNo"],
                "Status": row["status"],
                "Date": row["createdAt"],
                "Dept": row["dept"],
                "RAW": row.to_dict()
            })
            
    # Process Circulars
    for c in circs:
        unified_data.append({
            "ID": c.get("id") or c.get("number") or c.get("ref_no"),
            "Source": "Circular",
            "Type": "CIRCULAR",
            "Title": c.get("subject") or c.get("title") or "Unnamed Circular",
            "Ref No": c.get("number") or c.get("ref_no") or "N/A",
            "Status": "PUBLISHED",
            "Date": c.get("created_at") or c.get("date"),
            "Dept": c.get("dept") or c.get("category") or "General",
            "RAW": c
        })

    # Process MIS Files
    mis_archive = project_path("data", "mis", "archive")
    if mis_archive.exists():
        for f in mis_archive.glob("*.xlsx"):
            unified_data.append({
                "ID": f.name,
                "Source": "MIS Data Feed",
                "Type": "EXCEL_DATA",
                "Title": f.name,
                "Ref No": "N/A",
                "Status": "INGESTED",
                "Date": datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "Dept": "MIS",
                "RAW": {"filename": f.name, "path": str(f)}
            })
        
    df = pd.DataFrame(unified_data)
    if df.empty:
        st.warning("No documents found in the archive.")
        return

    # Apply Filters
    if doc_type != "All Types":
        df = df[df["Source"] == doc_type]
    if status_filter != "All":
        df = df[df["Status"] == status_filter]
    if search_query:
        df = df[
            df["Title"].str.contains(search_query, case=False, na=False) |
            df["Ref No"].astype(str).str.contains(search_query, case=False, na=False)
        ]

    # ─── ARCHIVE TABLE ────────────────────────────────────────────────────
    st.markdown(f"#### Results ({len(df)})")
    
    display_df = df[["Source", "Title", "Ref No", "Status", "Date", "Dept"]].copy()
    display_df["Date"] = pd.to_datetime(display_df["Date"], errors="coerce", utc=True).dt.strftime("%d-%b-%Y %H:%M")
    
    selection = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        key="archive_table"
    )

    if selection.selection.rows:
        selected_indices = selection.selection.rows
        
        if len(selected_indices) > 1:
            st.divider()
            st.subheader(f"💼 Bulk Operations Dashboard ({len(selected_indices)} selected)")
            
            selected_docs = df.iloc[selected_indices]
            with st.expander("👁️ View Selected Documents", expanded=False):
                st.table(selected_docs[["Source", "Title", "Ref No", "Dept"]])
                
            b_col1, b_col2 = st.columns(2)
            
            if b_col1.button("🗑️ Bulk Delete Permanently", use_container_width=True, type="secondary"):
                with st.spinner("Deleting selected documents..."):
                    deleted_count = 0
                    for r_idx in selected_indices:
                        doc = df.iloc[r_idx]
                        if doc["Source"] == "Office Note":
                            success = note_service.delete_note(doc["ID"])
                        elif doc["Source"] == "MIS Data Feed":
                            success = mis_service.delete_mis_file(doc["ID"])
                        elif doc["Source"] == "Circular":
                            success = circ_service.delete_circular(doc["ID"])
                        else:
                            success = False
                        if success:
                            deleted_count += 1
                    
                    st.success(f"Successfully deleted {deleted_count} of {len(selected_indices)} documents.")
                    st.rerun()
            
            import io
            import zipfile
            
            zip_buffer = io.BytesIO()
            has_pdfs = False
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for idx, r_idx in enumerate(selected_indices):
                    doc = df.iloc[r_idx]
                    pdf_bytes = None
                    filename = f"Document_{idx+1}.pdf"
                    
                    try:
                        if doc["Source"] == "Circular":
                            pdf_bytes = doc_service.generate_circular_pdf(doc["RAW"])
                            safe_ref = str(doc["Ref No"]).replace("/", "_").replace("\\", "_")
                            filename = f"Circular_{safe_ref}.pdf"
                            
                        elif doc["Source"] == "Office Note":
                            content = doc["RAW"].get("parsed_content", {})
                            if doc["Type"] == 'HIGH_VALUE_DD':
                                sig_snap = content.get("signatorySnapshot", {})
                                mapped_data = {
                                    "branch_sol": content.get("branchSol"),
                                    "applicant_name": content.get("applicantName"),
                                    "account_no": content.get("applicantAccount"),
                                    "kyc_status": content.get("kycCompliance", "YES"),
                                    "issue_date": content.get("dateOfIssue"),
                                    "beneficiary_name": content.get("beneficiaryName"),
                                    "dd_drawn_on": content.get("ddDrawnOn"),
                                    "amount": content.get("amount"),
                                    "txn_id": content.get("transactionId"),
                                    "purpose": content.get("purpose"),
                                    "circulars": content.get("policyCirculars", []),
                                    "recommendation": content.get("recommendation", "Approved as per guidelines."),
                                    "ref_no": doc["Ref No"],
                                    "note_date": content.get("noteDate"),
                                    "sig_init": sig_snap.get("initiator"),
                                    "sig_rec": sig_snap.get("recommender"),
                                    "sig_app": sig_snap.get("approver")
                                }
                                pdf_bytes = doc_service.generate_high_value_dd_pdf(mapped_data)
                            else:
                                prep_name = content.get('signatorySnapshot', {}).get('preparer', {}).get('name', 'Staff')
                                rev_list = content.get('signatorySnapshot', {}).get('reviewers', [])
                                sigs = [s.get('name') for s in rev_list] if isinstance(rev_list, list) else []
                                
                                intro, obs, recs = "", "", ""
                                if doc['Type'] == 'EXPENSE_APPROVAL':
                                    intro = f"Proposed expenditure of ₹{content.get('proposedAmount')} for {content.get('vendorName')}."
                                    obs = content.get('expensePurpose', '')
                                    recs = content.get('recommendation', '')
                                elif doc['Type'] == 'REVERSAL_CHARGES':
                                    intro = f"Proposal for reversal of {content.get('revChargeType')} in A/c {content.get('revAccountNumber')}."
                                    obs = content.get('revJustification', '')
                                    recs = f"We may reverse the amount of ₹{content.get('revReversalAmount')}."
                                else:
                                    obs = content.get('details', '')
                                
                                pdf_bytes = doc_service.generate_pdf_note(
                                    department=doc['Dept'], subject=doc['Title'],
                                    intro_text=intro, observations=obs, recommendations=recs, 
                                    prepared_by=prep_name, ref_no=doc['Ref No'],
                                    date=content.get('noteDate'), signatories=sigs, is_html=True
                                )
                            safe_ref = str(doc["Ref No"]).replace("/", "_").replace("\\", "_")
                            filename = f"Note_{safe_ref}.pdf"
                            
                        if pdf_bytes:
                            zf.writestr(filename, pdf_bytes)
                            has_pdfs = True
                    except Exception as e:
                        st.warning(f"Could not generate PDF for {doc['Title']}: {str(e)}")
            
            if has_pdfs:
                b_col2.download_button(
                    label="📥 Download Bulk PDFs (.zip)",
                    data=zip_buffer.getvalue(),
                    file_name=f"Bulk_Archive_{datetime.date.today().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                    type="primary"
                )
            else:
                b_col2.info("Selected items do not support PDF generation.")
        else:
            idx = selected_indices[0]
            selected_doc = df.iloc[idx]
            render_doc_manager(selected_doc, note_service, circ_service, mis_service, doc_service)

def render_doc_manager(doc, note_service, circ_service, mis_service, doc_service):
    st.divider()
    st.subheader(f"🛠️ Manager: {doc['Title']}")
    
    # Check if edit mode is active
    edit_key = f"edit_archive_{doc['ID']}"
    if st.session_state.get(edit_key):
        with st.form(f"form_edit_archive_{doc['ID']}", border=True):
            st.markdown("### ✏️ Edit Document Metadata")
            new_title = st.text_input("Title / Subject", value=doc["Title"])
            new_ref = st.text_input("Reference Number", value=doc["Ref No"])
            new_dept = st.text_input("Department", value=doc["Dept"])
            
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 Save Changes"):
                if doc["Source"] == "Circular":
                    circ_data = doc["RAW"]
                    circ_data["subject"] = new_title
                    circ_data["title"] = new_title
                    circ_data["number"] = new_ref
                    circ_data["ref_no"] = new_ref
                    circ_data["dept"] = new_dept
                    circ_data["category"] = new_dept
                    circ_service.save_circular(circ_data)
                    st.success("Circular metadata updated successfully!")
                elif doc["Source"] == "Office Note":
                    df_notes = pd.read_csv(note_service.csv_path)
                    note_row = df_notes[df_notes["id"] == doc["ID"]].iloc[0].to_dict()
                    parsed = json.loads(note_row["contentJson"]) if isinstance(note_row["contentJson"], str) else {}
                    parsed["deptName"] = new_dept
                    note_row["titleEn"] = new_title
                    note_row["referenceNo"] = new_ref
                    note_row["contentJson"] = json.dumps(parsed)
                    note_service.save_note(note_row)
                    st.success("Office Note metadata updated successfully!")
                
                del st.session_state[edit_key]
                st.rerun()
                
            if c2.form_submit_button("❌ Cancel"):
                del st.session_state[edit_key]
                st.rerun()
        return

    m_col1, m_col2 = st.columns([2, 1])
    
    with m_col1:
        with st.container(border=True):
            st.markdown(f"**Source Repository:** `{doc['Source']}`")
            st.markdown(f"**Reference Number:** `{doc['Ref No']}`")
            st.markdown(f"**Department:** {doc['Dept']}")
            st.markdown("---")
            if doc["Source"] == "Office Note":
                st.json(doc["RAW"].get("parsed_content", {}))
            else:
                st.json(doc["RAW"])

    with m_col2:
        pdf_bytes = None
        try:
            if doc["Source"] == "Circular":
                pdf_bytes = doc_service.generate_circular_pdf(doc["RAW"])
            elif doc["Source"] == "Office Note":
                content = doc["RAW"].get("parsed_content", {})
                if doc["Type"] == 'HIGH_VALUE_DD':
                    sig_snap = content.get("signatorySnapshot", {})
                    mapped_data = {
                        "branch_sol": content.get("branchSol"),
                        "applicant_name": content.get("applicantName"),
                        "account_no": content.get("applicantAccount"),
                        "kyc_status": content.get("kycCompliance", "YES"),
                        "issue_date": content.get("dateOfIssue"),
                        "beneficiary_name": content.get("beneficiaryName"),
                        "dd_drawn_on": content.get("ddDrawnOn"),
                        "amount": content.get("amount"),
                        "txn_id": content.get("transactionId"),
                        "purpose": content.get("purpose"),
                        "circulars": content.get("policyCirculars", []),
                        "recommendation": content.get("recommendation", "Approved as per guidelines."),
                        "ref_no": doc["Ref No"],
                        "note_date": content.get("noteDate"),
                        "sig_init": sig_snap.get("initiator"),
                        "sig_rec": sig_snap.get("recommender"),
                        "sig_app": sig_snap.get("approver")
                    }
                    pdf_bytes = doc_service.generate_high_value_dd_pdf(mapped_data)
                else:
                    prep_name = content.get('signatorySnapshot', {}).get('preparer', {}).get('name', 'Staff')
                    rev_list = content.get('signatorySnapshot', {}).get('reviewers', [])
                    sigs = [s.get('name') for s in rev_list] if isinstance(rev_list, list) else []
                    
                    intro, obs, recs = "", "", ""
                    if doc['Type'] == 'EXPENSE_APPROVAL':
                        intro = f"Proposed expenditure of ₹{content.get('proposedAmount')} for {content.get('vendorName')}."
                        obs = content.get('expensePurpose', '')
                        recs = content.get('recommendation', '')
                    elif doc['Type'] == 'REVERSAL_CHARGES':
                        intro = f"Proposal for reversal of {content.get('revChargeType')} in A/c {content.get('revAccountNumber')}."
                        obs = content.get('revJustification', '')
                        recs = f"We may reverse the amount of ₹{content.get('revReversalAmount')}."
                    else:
                        obs = content.get('details', '')
                    
                    pdf_bytes = doc_service.generate_pdf_note(
                        department=doc['Dept'], subject=doc['Title'],
                        intro_text=intro, observations=obs, recommendations=recs, 
                        prepared_by=prep_name, ref_no=doc['Ref No'],
                        date=content.get('noteDate'), signatories=sigs, is_html=True
                    )
        except Exception as e:
            st.error(f"Generation error: {str(e)}")
            
        if pdf_bytes:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"{doc['Source']}_{doc['Ref No'].replace('/', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        else:
            st.info("PDF generation not supported for this document type.")
            
        if st.button("✏️ Edit Metadata", use_container_width=True):
            st.session_state[f"edit_archive_{doc['ID']}"] = True
            st.rerun()
            
        if st.button("🗑️ Delete Permanently", use_container_width=True, type="secondary"):
            with st.spinner("Deleting document..."):
                if doc["Source"] == "Office Note":
                    success = note_service.delete_note(doc["ID"])
                elif doc["Source"] == "MIS Data Feed":
                    success = mis_service.delete_mis_file(doc["ID"])
                elif doc["Source"] == "Circular":
                    success = circ_service.delete_circular(doc["ID"])
                else:
                    success = False
                
                if success:
                    st.success("Document deleted successfully.")
                    st.rerun()
                else:
                    st.error("Delete failed or not implemented for this type.")

if __name__ == "__main__":
    render()
