from __future__ import annotations
import streamlit as st
import pandas as pd
import datetime
from src.interface.streamlit.components.primitives import render_action_bar
from src.interface.streamlit.state.services import get_doc_service_v4

def render() -> None:
    doc_service = get_doc_service_v4()
    render_action_bar("High Value DD Wizard", ["Strategic Approval", "Operational Scrutiny", "Policy Check"])

    # Initialize Wizard State
    if 'dd_step' not in st.session_state:
        st.session_state.dd_step = 0
    if 'dd_form' not in st.session_state:
        st.session_state.dd_form = {
            "refNo": f"RO/PLNG/{datetime.date.today().year}/{datetime.date.today().month:02d}/01",
            "date": datetime.date.today().strftime("%d.%m.%Y"),
            "noteType": "HIGH VALUE DEMAND DRAFT",
            "branchSOLID": "",
            "gradeOfHead": "MM III",
            "applicantName": "",
            "accountNumber": "",
            "kycCompliance": "Yes",
            "dateOfIssue": datetime.date.today(),
            "beneficiaryName": "",
            "amount": 0.0,
            "issuingBranch": "",
            "ddDrawnOn": "",
            "purpose": "",
            "transactionId": "",
            "policies": [
                {"department": "Inter Branch Reconciliation Division", "date": "02.04.2011", "ref": "1/2011-12"},
                {"department": "Banking Operations", "date": "01.11.2018", "ref": "Misc/452/2018-19"}
            ],
            "recommendation": "Since the branch request satisfies extant guidelines in the referred circulars, we may approve the entry in Finacle using HHVDD menu."
        }

    STEPS = ["Reference Info", "Branch Details", "Transaction", "Policy & Recommendation", "Finish"]
    
    # Progress Indicator
    cols = st.columns(len(STEPS))
    for i, step_name in enumerate(STEPS):
        with cols[i]:
            if i < st.session_state.dd_step:
                st.markdown(f"✅ <span style='color: #059669; font-size: 11px; font-weight: bold;'>{step_name}</span>", unsafe_allow_html=True)
            elif i == st.session_state.dd_step:
                st.markdown(f"🔵 <span style='color: #1e3a8a; font-size: 11px; font-weight: 900;'>{step_name}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"⚪ <span style='color: #94a3b8; font-size: 11px;'>{step_name}</span>", unsafe_allow_html=True)
    st.markdown("---")

    form = st.session_state.dd_form

    # Step 0: Reference Info
    if st.session_state.dd_step == 0:
        st.subheader("📝 Step 1: Reference Information")
        col1, col2 = st.columns(2)
        form["refNo"] = col1.text_input("Office Note Ref No", value=form["refNo"])
        form["date"] = col2.text_input("Note Date", value=form["date"])
        form["noteType"] = st.text_input("Note Type / Subject", value=form["noteType"])

    # Step 1: Branch Details
    elif st.session_state.dd_step == 1:
        st.subheader("🏛️ Step 2: Branch & Applicant Details")
        from src.infrastructure.persistence.master_repository import MasterRepository
        repo = MasterRepository()
        col1, col2 = st.columns(2)
        sol_input = col1.text_input("Branch SOL ID", value=form["branchSOLID"], max_chars=4, help="Enter 4-digit SOL ID")
        if sol_input != form["branchSOLID"]:
            form["branchSOLID"] = sol_input
            if sol_input and len(sol_input) >= 3:
                padded = sol_input.zfill(4)
                match = next((u for u in repo.get_by_category("UNIT") if u.code == padded), None)
                if match:
                    form["issuingBranch"] = match.name_en
                    meta = match.metadata or {}
                    if "gradeOfHead" in meta: form["gradeOfHead"] = meta["gradeOfHead"]
                else: form["issuingBranch"] = ""
            st.rerun()
        form["gradeOfHead"] = col2.selectbox("Grade of Branch Head", ["MM I", "MM II", "MM III", "SM I", "SM II", "TEG IV", "TEG V"], 
                                             index=["MM I", "MM II", "MM III", "SM I", "SM II", "TEG IV", "TEG V"].index(form.get("gradeOfHead", "MM III")))
        col3, col4 = st.columns(2)
        form["issuingBranch"] = col3.text_input("Issuing Branch Name", value=form["issuingBranch"])
        form["ddDrawnOn"] = col4.text_input("DD Drawn On (Payable Branch)", value=form["ddDrawnOn"])
        col5, col6 = st.columns(2)
        form["applicantName"] = col5.text_input("Applicant Name", value=form["applicantName"])
        form["accountNumber"] = col6.text_input("Account Number", value=form["accountNumber"])
        form["kycCompliance"] = st.selectbox("KYC Compliance", ["Yes", "No"], index=0 if form["kycCompliance"] == "Yes" else 1)

    # Step 2: Transaction Details
    elif st.session_state.dd_step == 2:
        st.subheader("💸 Step 3: Transaction Details")
        col1, col2 = st.columns(2)
        form["dateOfIssue"] = col1.date_input("Date of Issue", value=form["dateOfIssue"])
        form["transactionId"] = col2.text_input("Transaction ID", value=form["transactionId"])
        form["beneficiaryName"] = st.text_input("Beneficiary Name", value=form["beneficiaryName"])
        col3, col4 = st.columns(2)
        form["amount"] = col3.number_input("Amount (₹)", value=float(form["amount"]), min_value=0.0, format="%.2f")
        form["purpose"] = col4.text_input("Purpose of Transaction", value=form["purpose"])

    # Step 3: Policy & Recommendation
    elif st.session_state.dd_step == 3:
        st.subheader("📋 Step 4: Policy & Recommendation")
        st.markdown("#### Policy Circular References")
        if st.button("➕ Add Policy Row"):
            form["policies"].append({"department": "", "date": "", "ref": ""})
            st.rerun()
        for i, policy in enumerate(form["policies"]):
            c1, c2, c3, c4 = st.columns([2, 1, 1.5, 0.5])
            policy["department"] = c1.text_input(f"Dept {i+1}", value=policy["department"], key=f"d_{i}")
            policy["date"] = c2.text_input(f"Date {i+1}", value=policy.get("date", ""), key=f"dt_{i}")
            policy["ref"] = c3.text_input(f"Ref {i+1}", value=policy.get("ref", ""), key=f"r_{i}")
            if c4.button("🗑️", key=f"del_{i}"):
                form["policies"].pop(i)
                st.rerun()
        st.markdown("#### Final Recommendation")
        form["recommendation"] = st.text_area("Recommendation Text", value=form["recommendation"], height=100)

    # Step 4: Finish & Download
    elif st.session_state.dd_step == 4:
        st.subheader("✅ Step 5: Finalize & Download")
        st.success("Note configuration complete. You can now generate the official PDF document.")
        
        # Resolve live staff list and executives
        from src.interface.streamlit.state.services import get_master_service
        master_svc = get_master_service()
        all_staff = master_svc.get_by_category("STAFF")
        
        # Compile list of active RO staff members
        ro_staff_opts = sorted([
            f"{s.name_en} ({s.designation or 'Officer'})"
            for s in all_staff if str(s.metadata.get("sol")) == "3933" and s.username != "admin"
        ])
        if not ro_staff_opts:
            ro_staff_opts = ["Assistant Manager, GAD", "Chief Manager, GAD", "Regional Manager"]

        username = st.session_state.get("username", "Staff")
        curr_user_obj = next((u for u in all_staff if u.username == username), None)
        if curr_user_obj:
            default_initiator = f"{curr_user_obj.name_en} ({curr_user_obj.designation or 'Officer'})"
        else:
            default_initiator = "Assistant Manager, GAD"

        # Detect sensible defaults
        def_rec_idx = 0
        for idx, opt in enumerate(ro_staff_opts):
            if any(term in opt.upper() for term in ["CHIEF MANAGER", "AGM", "CHIEF"]):
                def_rec_idx = idx
                break
                
        def_app_idx = 0
        for idx, opt in enumerate(ro_staff_opts):
            if any(term in opt.upper() for term in ["SRM", "SENIOR REGIONAL", "CHIEF REGIONAL", "REGIONAL MANAGER", "RM"]):
                def_app_idx = idx
                break
        if def_app_idx == 0 and len(ro_staff_opts) > 1:
            def_app_idx = min(1, len(ro_staff_opts) - 1)

        # Dynamic Signatory configuration panel
        with st.expander("✍️ Signatory Configuration", expanded=True):
            col_s1, col_s2, col_s3 = st.columns(3)
            sig_init = col_s1.text_input("Initiator", value=default_initiator)
            sig_rec = col_s2.selectbox("Recommending Authority", options=ro_staff_opts, index=def_rec_idx)
            sig_app = col_s3.selectbox("Approving Authority", options=ro_staff_opts, index=def_app_idx)
        
        note_data = {
            "branch_sol": form["branchSOLID"],
            "applicant_name": form["applicantName"],
            "account_no": form["accountNumber"],
            "kyc_status": form["kycCompliance"].upper(),
            "issue_date": str(form["dateOfIssue"]),
            "beneficiary_name": form["beneficiaryName"],
            "dd_drawn_on": form["ddDrawnOn"],
            "amount": form["amount"],
            "txn_id": form["transactionId"],
            "purpose": form["purpose"],
            "circulars": form["policies"],
            "recommendation": form["recommendation"],
            "ref_no": form["refNo"],
            "note_date": form["date"],
            # Dynamic Signatory mappings
            "sig_init": sig_init,
            "sig_rec": sig_rec,
            "sig_app": sig_app
        }

        if st.button("📥 GENERATE & DOWNLOAD PDF", use_container_width=True, type="primary"):
            with st.spinner("Generating High-Fidelity PDF..."):
                pdf_bytes = doc_service.generate_high_value_dd_pdf(note_data)
                filename = f"DD_Note_{form['branchSOLID']}_{datetime.date.today().strftime('%d%m%Y')}.pdf"
                st.download_button(
                    label="📥 Click here to save PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
        
        from src.application.services.document.office_note_service import OfficeNoteService
        if st.button("💾 SAVE TO ARCHIVE", use_container_width=True):
            note_service = OfficeNoteService()
            new_note = {
                "type": "HIGH_VALUE_DD",
                "status": "DRAFT",
                "titleEn": f"HIGH VALUE DD - {note_data['applicant_name']}",
                "referenceNo": note_data['ref_no'],
                "parsed_content": {
                    "deptName": "PLANNING",
                    "branchSol": note_data['branch_sol'],
                    "applicantName": note_data['applicant_name'],
                    "applicantAccount": note_data['account_no'],
                    "kycCompliance": note_data['kyc_status'],
                    "dateOfIssue": note_data['issue_date'],
                    "beneficiaryName": note_data['beneficiary_name'],
                    "ddDrawnOn": note_data['dd_drawn_on'],
                    "amount": note_data['amount'],
                    "transactionId": note_data['txn_id'],
                    "purpose": note_data['purpose'],
                    "policyCirculars": note_data['circulars'],
                    "recommendation": note_data['recommendation'],
                    "noteDate": note_data['note_date'],
                    # Archive dynamic signatories
                    "signatorySnapshot": {
                        "initiator": sig_init,
                        "recommender": sig_rec,
                        "approver": sig_app
                    }
                }
            }
            note_service.save_note(new_note)
            st.success("Note archived successfully!")
        
        if st.button("🔄 Start New Note", use_container_width=True):
            del st.session_state.dd_form
            st.session_state.dd_step = 0
            st.rerun()

    # Navigation Buttons
    st.markdown("---")
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    if st.session_state.dd_step > 0 and st.session_state.dd_step < len(STEPS) - 1:
        if nav_col1.button("⬅️ Previous", use_container_width=True):
            st.session_state.dd_step -= 1
            st.rerun()
    if st.session_state.dd_step < len(STEPS) - 1:
        if nav_col3.button("Next ➡️", use_container_width=True):
            st.session_state.dd_step += 1
            st.rerun()
