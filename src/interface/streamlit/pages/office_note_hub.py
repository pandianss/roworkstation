from __future__ import annotations
import streamlit as st
import pandas as pd
import json
import datetime
from src.interface.streamlit.components.primitives import (
    render_action_bar, render_premium_metrics, render_data_table, render_chart_container
)
from src.interface.streamlit.state.services import get_doc_service_v4

from src.application.services.document.office_note_service import OfficeNoteService

def render():
    doc_service = get_doc_service_v4()
    note_service = OfficeNoteService()
    
    render_action_bar("Office Note Hub", ["Archive", "Search", "Management"])
    
    # Load Data via Service
    df = note_service.get_all()
    if df.empty:
        st.warning("No office notes found in the repository.")
        return
    
    # Dashboard Stats
    st.markdown("### 📊 Repository Insights")
    metrics = {
        "Total Notes": len(df),
        "Unique Types": df['type'].nunique(),
        "Departments": df['dept'].nunique(),
        "High Value DDs": len(df[df['type'] == 'HIGH_VALUE_DD'])
    }
    render_premium_metrics(metrics)
    
    # Filters
    st.markdown("### 🔍 Filters & Search")
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        selected_type = st.multiselect("Note Type", options=sorted(df['type'].unique().tolist()))
    with f_col2:
        selected_dept = st.multiselect("Department", options=sorted(df['dept'].unique().tolist()))
    with f_col3:
        search_query = st.text_input("Search Title or Reference", placeholder="Enter keywords...")
        
    filtered_df = df.copy()
    if selected_type:
        filtered_df = filtered_df[filtered_df['type'].isin(selected_type)]
    if selected_dept:
        filtered_df = filtered_df[filtered_df['dept'].isin(selected_dept)]
    if search_query:
        filtered_df = filtered_df[
            filtered_df['titleEn'].str.contains(search_query, case=False, na=False) |
            filtered_df['referenceNo'].str.contains(search_query, case=False, na=False)
        ]
        
    # Main Table
    st.markdown(f"#### Results ({len(filtered_df)})")
    
    display_cols = ['id', 'type', 'status', 'titleEn', 'dept', 'createdAt', 'referenceNo']
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    
    event = st.dataframe(
        filtered_df[available_cols],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="note_table"
    )
    
    if event.selection.rows:
        selected_row_idx = event.selection.rows[0]
        selected_note = filtered_df.iloc[selected_row_idx]
        render_note_details(selected_note, doc_service, note_service)

def render_note_details(note, doc_service, note_service):
    st.divider()
    
    # Check if in editing mode
    edit_key = f"edit_{note['id']}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    if st.session_state[edit_key]:
        render_edit_form(note, note_service)
        if st.button("Cancel Editing", key=f"cancel_{note['id']}"):
            st.session_state[edit_key] = False
            st.rerun()
        return

    st.subheader(f"📄 Note Details: {note['titleEn']}")
    
    content = note['parsed_content']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container(border=True):
            st.markdown(f"**Reference:** `{note.get('referenceNo', 'N/A')}`")
            st.markdown(f"**Type:** `{note['type']}` | **Status:** `{note['status']}`")
            st.markdown(f"**Department:** {note['dept']}")
            st.markdown("---")
            
            from src.core.utils.number_utils import format_indian_number
            # Type-specific rendering
            if note['type'] == 'HIGH_VALUE_DD':
                st.markdown("#### High Value DD Info")
                st.write(f"**Applicant:** {content.get('applicantName', 'N/A')}")
                st.write(f"**Account:** {content.get('applicantAccount', 'N/A')}")
                amount = content.get('amount', '0')
                amount_fmt = format_indian_number(amount, include_symbol=True)
                st.write(f"**Amount:** {amount_fmt}")
                st.write(f"**Beneficiary:** {content.get('beneficiaryName', 'N/A')}")
                st.write(f"**Purpose:** {content.get('purpose', 'N/A')}")
                st.write(f"**Transaction ID:** {content.get('transactionId', 'N/A')}")
            
            elif note['type'] == 'EXPENSE_APPROVAL':
                st.markdown("#### Expense Details")
                st.write(f"**Budget Head:** {content.get('budgetHead', 'N/A')}")
                p_amt = format_indian_number(content.get('proposedAmount', '0'), include_symbol=True)
                st.write(f"**Proposed Amount:** {p_amt}")
                st.write(f"**Vendor:** {content.get('vendorName', 'N/A')}")
                st.markdown("**Purpose:**")
                st.write(content.get('expensePurpose', 'N/A'))
                st.markdown("**Recommendation:**")
                st.write(content.get('recommendation', 'N/A'))

            elif note['type'] == 'REVERSAL_CHARGES':
                st.markdown("#### Reversal Details")
                st.write(f"**Account:** {content.get('revAccountNumber', 'N/A')}")
                st.write(f"**Charge Type:** {content.get('revChargeType', 'N/A')}")
                r_amt = format_indian_number(content.get('revReversalAmount', '0'), include_symbol=True)
                st.write(f"**Reversal Amount:** {r_amt}")
                st.markdown("**Justification:**")
                st.write(content.get('revJustification', 'N/A'))
            
            elif note['type'] == 'CUSTOM':
                st.markdown("#### Content Preview")
                details = content.get('details', '')
                if details:
                    st.components.v1.html(f"<div style='color: white; font-family: sans-serif;'>{details}</div>", height=400, scrolling=True)
                else:
                    st.info("No detailed content available in preview.")
            
            else:
                st.markdown("#### Raw Data")
                st.json(content)

    with col2:
        st.markdown("#### Actions")
        
        c1, c2 = st.columns(2)
        if c1.button("✏️ Edit Note", use_container_width=True, key=f"edit_btn_{note['id']}"):
            st.session_state[edit_key] = True
            st.rerun()
            
        if c2.button("🗑️ Delete", use_container_width=True, key=f"del_btn_{note['id']}", type="secondary"):
            if note_service.delete_note(note['id']):
                st.success("Note deleted and reference numbers adjusted.")
                st.rerun()
            else:
                st.error("Failed to delete note.")

        st.divider()
        
        if st.button("🔄 Regenerate PDF", use_container_width=True, type="primary"):
            pdf_bytes = None
            with st.spinner("Generating PDF..."):
                try:
                    if note['type'] == 'HIGH_VALUE_DD':
                        # Map CSV keys to service keys
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
                            "ref_no": note["referenceNo"],
                            "note_date": content.get("noteDate"),
                            "sig_init": sig_snap.get("initiator"),
                            "sig_rec": sig_snap.get("recommender"),
                            "sig_app": sig_snap.get("approver")
                        }
                        pdf_bytes = doc_service.generate_high_value_dd_pdf(mapped_data)
                    
                    elif note['type'] in ['CUSTOM', 'EXPENSE_APPROVAL', 'REVERSAL_CHARGES']:
                        prep_name = content.get('signatorySnapshot', {}).get('preparer', {}).get('name', 'Staff')
                        rev_list = content.get('signatorySnapshot', {}).get('reviewers', [])
                        sigs = [s.get('name') for s in rev_list] if isinstance(rev_list, list) else []
                        
                        intro, obs, recs = "", "", ""
                        if note['type'] == 'EXPENSE_APPROVAL':
                            intro = f"Proposed expenditure of ₹{content.get('proposedAmount')} for {content.get('vendorName')}."
                            obs = content.get('expensePurpose', '')
                            recs = content.get('recommendation', '')
                        elif note['type'] == 'REVERSAL_CHARGES':
                            intro = f"Proposal for reversal of {content.get('revChargeType')} in A/c {content.get('revAccountNumber')}."
                            obs = content.get('revJustification', '')
                            recs = f"We may reverse the amount of ₹{content.get('revReversalAmount')}."
                        else:
                            obs = content.get('details', '')
                        
                        pdf_bytes = doc_service.generate_pdf_note(
                            department=note['dept'], subject=note['titleEn'],
                            intro_text=intro, observations=obs, recommendations=recs, 
                            prepared_by=prep_name, ref_no=note['referenceNo'],
                            date=content.get('noteDate'), signatories=sigs, is_html=True
                        )
                except Exception as e:
                    st.error(f"Failed to generate PDF: {str(e)}")
            
            if pdf_bytes:
                st.download_button("📥 Download PDF", data=pdf_bytes, file_name=f"Note_{note['id'][:8]}.pdf", mime="application/pdf", use_container_width=True)

        if st.button("📋 Copy Raw JSON", use_container_width=True):
            st.code(json.dumps(content, indent=2), language="json")

def render_edit_form(note, note_service):
    st.subheader(f"✏️ Editing: {note['titleEn']}")
    with st.form(f"form_edit_{note['id']}"):
        new_title = st.text_input("Note Title", value=note['titleEn'])
        new_status = st.selectbox("Status", ["DRAFT", "PENDING", "FINALIZED"], index=["DRAFT", "PENDING", "FINALIZED"].index(note['status']))
        
        st.markdown("#### Note Content (JSON Editor)")
        st.caption("Advanced: Modify the underlying data structure.")
        content_json_str = st.text_area("Content Payload", value=json.dumps(note['parsed_content'], indent=2), height=300)
        
        if st.form_submit_button("💾 Save Changes", use_container_width=True):
            try:
                new_content = json.loads(content_json_str)
                updated_note = dict(note)
                updated_note['titleEn'] = new_title
                updated_note['status'] = new_status
                updated_note['parsed_content'] = new_content
                # Remove extra columns before saving
                updated_note.pop('dept', None)
                updated_note.pop('created_at_dt', None)
                
                note_service.save_note(updated_note)
                st.success("Changes saved successfully!")
                st.session_state[f"edit_{note['id']}"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save: {str(e)}")


if __name__ == "__main__":
    render()
