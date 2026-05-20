from __future__ import annotations
import datetime
import json
import pandas as pd
import streamlit as st
from src.application.services.wizard_service import WizardService
from src.core.utils.number_utils import format_indian_number
from src.interface.streamlit.state.services import (
    get_doc_service_v4, get_circular_service, get_master_service, get_mm_service, get_task_service
)
from src.interface.streamlit.components.primitives import render_action_bar
from src.interface.streamlit.components.doc_components import render_wizard_tile, render_document_card

def render() -> None:
    render_action_bar("Document Hub & Command Center", ["Generation", "Archive", "Insights"])

    tabs = st.tabs(["✨ Document Generation", "📁 Master Archive", "📊 Analytics"])
    
    with tabs[0]:
        if "wizard_selection" not in st.session_state:
            st.session_state["wizard_selection"] = None

        if st.session_state["wizard_selection"] is None:
            render_unified_gallery()
        else:
            if st.button("⬅️ Back to Gallery", key="back_to_gallery"):
                st.session_state["wizard_selection"] = None
                # Clear all wizard data keys
                for key in list(st.session_state.keys()):
                    if any(x in key for x in ["data", "step", "last_pdf"]):
                        del st.session_state[key]
                st.rerun()
            render_selected_wizard()
            
    with tabs[1]:
        render_enhanced_archive()
        
    with tabs[2]:
        render_document_insights()

def render_unified_gallery() -> None:
    st.markdown("### 🛠️ Document & Operations Toolkit")
    st.caption("Select a specialized generator or operational wizard to begin.")

    categories = {
        "Official Correspondence": [
            {"id": "circular_drafter", "title": "Circular Drafter", "desc": "Draft and issue official regional circulars with auto-indexing.", "icon": "📜"},
            {"id": "office_note", "title": "Office Note Wizard", "desc": "Draft, format, and generate official trilingual office notes.", "icon": "📝"},
            {"id": "letter_generator", "title": "Letter Generator", "desc": "Draft and generate general official letters.", "icon": "✉️", "nav_to_page": True},
            {"id": "office_note_hub", "title": "Office Note Hub", "desc": "Manage and track office notes.", "icon": "📝", "nav_to_page": True},
            {"id": "mail_merge", "title": "Bulk Mail Merge", "desc": "Personalized documents from Excel data.", "icon": "📬"},
        ],
        "Returns & Compliance": [
            {"id": "rbi_proforma", "title": "RBI Proforma", "desc": "Report branch openings/updates to RBI.", "icon": "🏦"},
            {"id": "statutory_returns", "title": "Statutory Tracker", "desc": "Monitor periodic return submissions.", "icon": "🛡️"},
        ],
        "Operational Wizards": [
            {"id": "high_value_dd", "title": "High Value DD Note", "desc": "Report and approve high value DDs.", "icon": "💸", "nav_to_page": True},
            {"id": "broken_interest", "title": "Broken Interest", "desc": "Calculate interest for non-standard periods.", "icon": "📈"},
            {"id": "expense_approval", "title": "Expense Approval", "desc": "Request approval for admin expenses.", "icon": "💸"},
            {"id": "gl_activation", "title": "GL Activation", "desc": "Activate or modify General Ledger heads.", "icon": "📒"},
            {"id": "reversal_charges", "title": "Charge Reversal", "desc": "Request waiver or reversal of bank charges.", "icon": "🔄"},
        ],
        "Branch Support": [
            {"id": "visiting_card", "title": "Visiting Card Wizard", "desc": "Generate printable staff visiting cards.", "icon": "🪪", "nav_to_page": True},
            {"id": "anniversary_note", "title": "Anniversary Note", "desc": "Generate branch anniversary greetings.", "icon": "🎉"},
            {"id": "branch_visits", "title": "Visit Report", "desc": "Record Region Head branch visit observations.", "icon": "🚗"},
            {"id": "micr_request", "title": "MICR/Cheque", "desc": "Request MICR codes or cheque series.", "icon": "🎫"},
            {"id": "proforma_branch", "title": "Branch Code", "desc": "Core banking setup data for branches.", "icon": "🏢"},
        ]
    }

    for cat_name, wizard_list in categories.items():
        st.subheader(cat_name)
        cols = st.columns(3)
        for i, wizard in enumerate(wizard_list):
            with cols[i % 3]:
                if render_wizard_tile(wizard['icon'], wizard['title'], wizard['desc'], wizard['id']):
                    if wizard.get("nav_to_page"):
                        st.session_state["requested_page"] = wizard["title"]
                        st.session_state["wizard_selection"] = None
                        st.rerun()
                    else:
                        st.session_state["wizard_selection"] = wizard['id']
                        st.rerun()

def render_selected_wizard() -> None:
    wid = st.session_state["wizard_selection"]
    
    # Map to form functions
    if wid == "broken_interest":
        render_broken_interest_wizard()
    elif wid == "dicgc":
        from src.interface.streamlit.pages import dicgc
        dicgc.render()
    elif wid == "statutory_returns":
        from src.interface.streamlit.pages import returns
        returns.render()
    elif wid == "branch_visits":
        from src.interface.streamlit.pages import visits
        visits.render()
    elif wid == "office_note":
        render_office_note_wizard()
    elif wid == "circular_drafter":
        render_circular_drafter_wizard()
    elif wid == "anniversary_note":
        render_anniversary_note_wizard()
    elif wid == "mail_merge":
        render_mail_merge_wizard()
    elif wid == "high_value_dd":
        render_high_value_dd_wizard()
    elif wid == "micr_request":
        render_micr_request_wizard()
    elif wid == "proforma_branch":
        render_proforma_branch_wizard()
    elif wid == "reversal_charges":
        render_reversal_charges_wizard()
    elif wid == "rbi_proforma":
        render_rbi_proforma_wizard()
    elif wid == "expense_approval":
        render_expense_approval_wizard()
    elif wid == "gl_activation":
        render_gl_activation_wizard()
    else:
        st.info(f"Wizard '{wid}' is being integrated.")

@st.fragment
def render_enhanced_archive() -> None:
    st.markdown("### 🗄️ Unified Master Archive")
    
    svc = WizardService()
    
    # Advanced Filtering UI
    c1, c2, c3 = st.columns([2, 1, 1])
    search = c1.text_input("🔍 Search Subject, Reference or Author", placeholder="Type to filter...")
    
    types = ["All", "Circular Drafter", "Office Note", "Broken Interest", "RBI Proforma", "Expense Approval", "GL Activation", "DICGC Return", "High Value DD"]
    type_filter = c2.selectbox("Type Filter", types)
    
    # Load filtered data
    submissions = svc.get_filtered_submissions(search=search, wizard_type=None if type_filter == "All" else type_filter)
    
    if not submissions:
        st.info("No documents match your search criteria.")
        return

    st.caption(f"Showing {len(submissions)} documents")
    st.divider()

    for s in submissions:
        # Render using the new premium card component
        pdf_btn, edit_btn, del_btn = render_document_card(
            doc_type=s.wizard_type.replace('_', ' ').upper(),
            subject=s.subject or "Untitled Document",
            reference=s.reference_no or "DRAFT",
            date=s.created_at.strftime("%d.%m.%Y"),
            author=s.submitted_by,
            key=s.id
        )
        
        # Action Handlers
        if pdf_btn:
            handle_archive_pdf_gen(s)
        
        if edit_btn:
            handle_archive_edit(s)
            
        if del_btn:
            if svc.delete_submission(s.id):
                st.success("Document removed.")
                st.rerun()

def handle_archive_pdf_gen(s):
    with st.spinner("Preparing PDF..."):
        doc_svc = get_doc_service_v4()
        content = json.loads(s.content_json)
        pdf = doc_svc.generate_wizard_pdf(
            wizard_type=s.wizard_type,
            data=content,
            submitted_by=s.submitted_by,
            subject=s.subject,
            ref=s.reference_no
        )
        st.download_button(
            "💾 Download Generated PDF",
            data=pdf,
            file_name=f"{s.wizard_type.upper()}_{s.id[:8]}.pdf",
            mime="application/pdf",
            key=f"dl_final_{s.id}"
        )

def handle_archive_edit(s):
    wiz_id = s.wizard_type
    st.session_state["wizard_selection"] = wiz_id
    data_key_map = {
        "broken_interest": "wiz_data",
        "expense_approval": "exp_data",
        "gl_activation": "gl_data",
        "rbi_proforma": "rbi_data",
        "high_value_dd": "dd_data",
        "micr_request": "micr_data",
        "reversal_charges": "rev_data"
    }
    key = data_key_map.get(wiz_id)
    if key:
        st.session_state[key] = json.loads(s.content_json)
        st.session_state[key.replace('data', 'step')] = 1
    st.rerun()

def render_document_insights() -> None:
    st.markdown("### 📊 Document Insights")
    svc = WizardService()
    subs = svc.get_submissions()
    if not subs:
        st.info("No data available for analytics.")
        return
        
    df = pd.DataFrame([{
        "type": s.wizard_type.replace('_', ' ').title(),
        "date": s.created_at.date()
    } for s in subs])
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Volume by Type")
        type_counts = df["type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        st.bar_chart(type_counts.set_index("Type"))
        
    with c2:
        st.markdown("#### Daily Activity")
        daily = df.groupby("date").size().reset_index(name="count")
        st.line_chart(daily.set_index("date"))

# --- MIGRATED WIZARD FORMS ---

def render_office_note_wizard() -> None:
    from src.interface.streamlit.pages.execution import render_office_note_tab
    render_office_note_tab(get_doc_service_v4(), get_master_service)

def render_circular_drafter_wizard() -> None:
    from src.interface.streamlit.pages.execution import render_circular_management_tab
    render_circular_management_tab(get_circular_service(), get_doc_service_v4())

def render_anniversary_note_wizard() -> None:
    st.markdown("### 🎂 Branch Anniversary Note")
    doc_service = get_doc_service_v4()
    with st.form("anniversary_note_form_wiz"):
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

def render_mail_merge_wizard() -> None:
    from src.interface.streamlit.pages.execution import render_mail_merge_tab
    render_mail_merge_tab(get_mm_service())

def render_broken_interest_wizard() -> None:
    st.markdown("### 📈 Broken Period Interest Calculator")
    if "wiz_step" not in st.session_state: st.session_state["wiz_step"] = 1
    if "wiz_data" not in st.session_state:
        st.session_state["wiz_data"] = {
            "depositor_type": "Individual", "category": "General", "cif_id": "", "account_no": "",
            "open_date": datetime.date.today(), "dob": datetime.date(1980, 1, 1), "age": 0,
            "principal": 100000.0, "base_rate": 6.50, "spread": 0.0, "effective_rate": 6.50,
            "start_date": datetime.date.today() - datetime.timedelta(days=30),
            "end_date": datetime.date.today(), "days": 30, "frequency": "SIMPLE",
            "interest_amount": 0.0, "justification": ""
        }
    data = st.session_state["wiz_data"]
    if st.session_state["wiz_step"] == 1:
        st.markdown("#### Step 1: Depositor & Account Details")
        col1, col2 = st.columns(2)
        data["depositor_type"] = col1.selectbox("Depositor Type", ["Individual", "Organization"])
        data["category"] = col2.selectbox("Customer Category", ["General", "Senior Citizen", "Super Senior Citizen"])
        data["cif_id"] = col1.text_input("CIF ID", value=data["cif_id"])
        data["account_no"] = col2.text_input("Account Number", value=data["account_no"])
        data["open_date"] = col1.date_input("Open Date", value=data["open_date"])
    elif st.session_state["wiz_step"] == 2:
        st.markdown("#### Step 2: Rate & Period")
        col1, col2 = st.columns(2)
        data["principal"] = col1.number_input("Principal (₹)", value=data["principal"])
        data["base_rate"] = col2.number_input("Base Rate (%)", value=data["base_rate"])
        data["start_date"] = col1.date_input("Start Date", value=data["start_date"])
        data["end_date"] = col2.date_input("End Date", value=data["end_date"])
        data["days"] = (data["end_date"] - data["start_date"]).days
        st.metric("Total Days", f"{data['days']} days")
    elif st.session_state["wiz_step"] == 3:
        st.markdown("#### Step 3: Finalize")
        svc = WizardService()
        data["interest_amount"] = svc.calculate_broken_period_interest(data["principal"], data["base_rate"], data["days"])
        st.success(f"Interest: {format_indian_number(data['interest_amount'], include_symbol=True)}")
        if st.button("💾 Save Submission"):
            svc.save_submission("broken_interest", st.session_state.get("username", "USER"), data, subject=f"Interest: {data['account_no']}")
            st.success("Saved!")

    # Generic Nav
    st.divider()
    c1, c2 = st.columns(2)
    if st.session_state["wiz_step"] > 1 and c1.button("⬅️ Previous", key="nav_prev"):
        st.session_state["wiz_step"] -= 1
        st.rerun()
    if st.session_state["wiz_step"] < 3 and c2.button("Next ➡️", key="nav_next"):
        st.session_state["wiz_step"] += 1
        st.rerun()

def render_expense_approval_wizard() -> None:
    st.markdown("### 💸 Expense Approval Wizard")
    if "exp_step" not in st.session_state: st.session_state["exp_step"] = 1
    if "exp_data" not in st.session_state:
        st.session_state["exp_data"] = {
            "category": "REVENUE", "budget_head": "Repairs", "custom_head": "",
            "allocated": 0.0, "utilized": 0.0, "purpose": "", "amount": 0.0,
            "quotation_basis": "L1", "vendor_name": "", "recommendation": ""
        }
    exp = st.session_state["exp_data"]
    if st.session_state["exp_step"] == 1:
        st.markdown("#### Step 1: Categorization")
        exp["category"] = st.selectbox("Category", ["REVENUE", "CAPITAL"])
        exp["budget_head"] = st.selectbox("Head", ["Repairs", "Printing", "Legal", "Other"])
        exp["amount"] = st.number_input("Amount (₹)", value=exp["amount"])
    elif st.session_state["exp_step"] == 2:
        st.markdown("#### Step 2: Vendor")
        exp["vendor_name"] = st.text_input("Vendor", value=exp["vendor_name"])
        exp["purpose"] = st.text_area("Purpose", value=exp["purpose"])
    elif st.session_state["exp_step"] == 3:
        st.markdown("#### Step 3: Finalize")
        if st.button("💾 Submit Expense"):
            svc = WizardService()
            svc.save_submission("expense_approval", st.session_state.get("username", "USER"), exp, subject=f"Expense: {exp['budget_head']}")
            st.success("Submitted!")

    st.divider()
    c1, c2 = st.columns(2)
    if st.session_state["exp_step"] > 1 and c1.button("⬅️ Previous", key="exp_nav_prev"):
        st.session_state["exp_step"] -= 1
        st.rerun()
    if st.session_state["exp_step"] < 3 and c2.button("Next ➡️", key="exp_nav_next"):
        st.session_state["exp_step"] += 1
        st.rerun()

def render_gl_activation_wizard() -> None:
    st.markdown("### 📒 GL Activation Wizard")
    if "gl_step" not in st.session_state: st.session_state["gl_step"] = 1
    if "gl_data" not in st.session_state:
        st.session_state["gl_data"] = {"account_no": "", "desc": "", "purpose": ""}
    gl = st.session_state["gl_data"]
    if st.session_state["gl_step"] == 1:
        gl["account_no"] = st.text_input("Proposed GL", value=gl["account_no"])
        gl["desc"] = st.text_input("GL Name", value=gl["desc"])
    elif st.session_state["gl_step"] == 2:
        gl["purpose"] = st.text_area("Purpose", value=gl["purpose"])
        if st.button("💾 Submit GL"):
            svc = WizardService()
            svc.save_submission("gl_activation", st.session_state.get("username", "USER"), gl, subject=f"GL: {gl['desc']}")
            st.success("Submitted!")
    st.divider()
    c1, c2 = st.columns(2)
    if st.session_state["gl_step"] > 1 and c1.button("⬅️ Previous", key="gl_nav_prev"):
        st.session_state["gl_step"] -= 1
        st.rerun()
    if st.session_state["gl_step"] < 2 and c2.button("Next ➡️", key="gl_nav_next"):
        st.session_state["gl_step"] += 1
        st.rerun()

def render_rbi_proforma_wizard() -> None:
    st.markdown("### 🏦 RBI Proforma Reporting Wizard")
    
    if "rbi_step" not in st.session_state: st.session_state["rbi_step"] = 1
    if "rbi_data" not in st.session_state:
        st.session_state["rbi_data"] = {
            "action": "ADDITION", "outlet_class": "BM_BRANCH",
            "update_part_i": "", "update_eff_date": datetime.date.today(),
            "conv_from": "", "conv_to": "", "conv_part_i": "", "conv_date": datetime.date.today(),
            "bm_domestic": "DOMESTIC",
            "bc_type": "CORPORATE", "bc_base_part_i": "", "bc_iba_reg": "",
            "office_domestic": "DOMESTIC", "office_type": "", "office_type_other": "", "office_base_part_i": "",
            "naio_type": "", "naio_type_other": "", "naio_base_part_i": "",
            "csp_mode": "", "csp_mode_other": "", "csp_onsite": "ONSITE", "csp_manned": "MANNED", "csp_base_part_i": "",
            "outlet_name": "", "app_category": "GENERAL_PERMISSION", "opening_date": datetime.date.today(),
            "licence_no": "", "licence_date": datetime.date.today(), "reval_ref": "", "reval_date": datetime.date.today(),
            "currency_chest_part_i": "",
            "micr": "", "ifsc": "", "cbs_code": "",
            "country": "INDIA", "state": "TAMIL NADU", "district": "DINDIGUL", "sub_district": "", "revenue_centre": "",
            "addr1": "", "addr2": "", "post_office": "", "pin": "",
            "long": "", "lat": "",
            "contact_name": "", "tel": "", "mobile": "", "fax": "", "email": "",
            "working_type": "FULL_TIME", "full_time_hours": "10:00 - 16:00, Mon-Sat",
            "schedule": {}, # For part-time
            "additional_centres": "",
            "services": {}, # Checkboxes
            "forex_ad_cat": "", "forex_auth_date": datetime.date.today(), "forex_settling_part_i": "",
            "remarks": ""
        }
    
    rbi = st.session_state["rbi_data"]
    
    if st.session_state["rbi_step"] == 1:
        st.markdown("#### Step 1: Action & Outlet Class")
        col1, col2 = st.columns(2)
        rbi["action"] = col1.selectbox("Action", ["ADDITION", "UPDATION", "CLOSURE", "MERGED", "CONVERSION"])
        rbi["outlet_class"] = col2.selectbox("Outlet Class", ["BM_BRANCH", "FIXED_BC", "OFFICE", "NAIO", "OTHER_CSP"])
    elif st.session_state["rbi_step"] == 2:
        st.markdown(f"#### Step 2: {rbi['outlet_class']} Details")
        if rbi["outlet_class"] == "BM_BRANCH":
            rbi["bm_domestic"] = st.selectbox("Domestic / Overseas", ["DOMESTIC", "OVERSEAS"])
        else:
            st.info("Class specific details entry enabled.")
    elif st.session_state["rbi_step"] == 3:
        st.markdown("#### Step 3: Identity")
        rbi["outlet_name"] = st.text_input("Name of Outlet *", value=rbi["outlet_name"])
        rbi["opening_date"] = st.date_input("Opening Date", value=rbi["opening_date"])
    elif st.session_state["rbi_step"] == 4:
        st.markdown("#### Step 4: Location")
        rbi["addr1"] = st.text_input("Address Line 1", value=rbi["addr1"])
        rbi["pin"] = st.text_input("Pin Code", value=rbi["pin"])
    elif st.session_state["rbi_step"] == 5:
        st.markdown("#### Step 5: Operations")
        rbi["working_type"] = st.radio("Working Days", ["FULL_TIME", "PART_TIME"])
    elif st.session_state["rbi_step"] == 6:
        st.markdown("#### Step 6: Finalize")
        if st.button("🚀 Submit RBI Proforma"):
            svc = WizardService()
            svc.save_submission("rbi_proforma", st.session_state.get("username", "USER"), rbi, subject=f"RBI: {rbi['outlet_name']}")
            st.success("Submitted!")

    st.divider()
    c1, c2 = st.columns(2)
    if st.session_state["rbi_step"] > 1 and c1.button("⬅️ Previous", key="rbi_nav_prev"):
        st.session_state["rbi_step"] -= 1
        st.rerun()
    if st.session_state["rbi_step"] < 6 and c2.button("Next ➡️", key="rbi_nav_next"):
        st.session_state["rbi_step"] += 1
        st.rerun()

def render_reversal_charges_wizard() -> None:
    st.markdown("### 🔄 Charge Reversal Wizard")
    if "rev_step" not in st.session_state: st.session_state["rev_step"] = 1
    if "rev_data" not in st.session_state:
        st.session_state["rev_data"] = {"account_no": "", "charge_type": "SMS Charges", "amount": 0.0, "justification": ""}
    rev = st.session_state["rev_data"]
    if st.session_state["rev_step"] == 1:
        rev["account_no"] = st.text_input("Account No", value=rev["account_no"])
    elif st.session_state["rev_step"] == 2:
        rev["charge_type"] = st.selectbox("Charge Type", ["SMS Charges", "LRS", "AMC", "Penalty", "Other"])
        rev["amount"] = st.number_input("Amount (₹)", value=rev["amount"])
    elif st.session_state["rev_step"] == 3:
        rev["justification"] = st.text_area("Justification", value=rev["justification"])
        if st.button("💾 Submit Reversal"):
            svc = WizardService()
            svc.save_submission("reversal_charges", st.session_state.get("username", "USER"), rev, subject=f"Reversal: {rev['account_no']}")
            st.success("Submitted!")
    st.divider()
    c1, c2 = st.columns(2)
    if st.session_state["rev_step"] > 1 and c1.button("⬅️ Previous", key="rev_nav_prev"):
        st.session_state["rev_step"] -= 1
        st.rerun()
    if st.session_state["rev_step"] < 3 and c2.button("Next ➡️", key="rev_nav_next"):
        st.session_state["rev_step"] += 1
        st.rerun()

def render_micr_request_wizard() -> None:
    st.markdown("### 🎫 MICR/Cheque Request Wizard")
    if "micr_step" not in st.session_state: st.session_state["micr_step"] = 1
    if "micr_data" not in st.session_state:
        st.session_state["micr_data"] = {"branch_name": "", "purpose": ""}
    micr = st.session_state["micr_data"]
    if st.session_state["micr_step"] == 1:
        micr["branch_name"] = st.text_input("Branch Name", value=micr["branch_name"])
    elif st.session_state["micr_step"] == 2:
        micr["purpose"] = st.text_area("Purpose", value=micr["purpose"])
        if st.button("💾 Submit MICR Request"):
            svc = WizardService()
            svc.save_submission("micr_request", st.session_state.get("username", "USER"), micr, subject=f"MICR: {micr['branch_name']}")
            st.success("Submitted!")
    st.divider()
    c1, c2 = st.columns(2)
    if st.session_state["micr_step"] > 1 and c1.button("⬅️ Previous", key="micr_nav_prev"):
        st.session_state["micr_step"] -= 1
        st.rerun()
    if st.session_state["micr_step"] < 2 and c2.button("Next ➡️", key="micr_nav_next"):
        st.session_state["micr_step"] += 1
        st.rerun()

def render_proforma_branch_wizard() -> None:
    st.markdown("### 🏢 Proforma Branch Code Wizard")
    if "prof_step" not in st.session_state: st.session_state["prof_step"] = 1
    if "prof_data" not in st.session_state:
        st.session_state["prof_data"] = {"branch_name": "", "postal_address": ""}
    prof = st.session_state["prof_data"]
    if st.session_state["prof_step"] == 1:
        prof["branch_name"] = st.text_input("Branch Name", value=prof["branch_name"])
    elif st.session_state["prof_step"] == 2:
        prof["postal_address"] = st.text_area("Address", value=prof["postal_address"])
        if st.button("💾 Submit Proforma"):
            svc = WizardService()
            svc.save_submission("proforma_branch", st.session_state.get("username", "USER"), prof, subject=f"Proforma: {prof['branch_name']}")
            st.success("Submitted!")
    st.divider()
    c1, c2 = st.columns(2)
    if st.session_state["prof_step"] > 1 and c1.button("⬅️ Previous", key="prof_nav_prev"):
        st.session_state["prof_step"] -= 1
        st.rerun()
    if st.session_state["prof_step"] < 2 and c2.button("Next ➡️", key="prof_nav_next"):
        st.session_state["prof_step"] += 1
        st.rerun()

def render_high_value_dd_wizard() -> None:
    st.markdown("### ✉️ High Value DD Reporting Wizard")
    if "dd_step" not in st.session_state: st.session_state["dd_step"] = 1
    if "dd_data" not in st.session_state:
        st.session_state["dd_data"] = {"applicant_name": "", "beneficiary": "", "amount": 0.0}
    dd = st.session_state["dd_data"]
    if st.session_state["dd_step"] == 1:
        dd["applicant_name"] = st.text_input("Applicant", value=dd["applicant_name"])
        dd["beneficiary"] = st.text_input("Beneficiary", value=dd["beneficiary"])
    elif st.session_state["dd_step"] == 2:
        dd["amount"] = st.number_input("Amount (₹)", value=dd["amount"])
        if st.button("🚀 Submit DD Report"):
            svc = WizardService()
            svc.save_submission("high_value_dd", st.session_state.get("username", "USER"), dd, subject=f"DD: {dd['beneficiary']}")
            st.success("Submitted!")
    st.divider()
    c1, c2 = st.columns(2)
    if st.session_state["dd_step"] > 1 and c1.button("⬅️ Previous", key="dd_nav_prev"):
        st.session_state["dd_step"] -= 1
        st.rerun()
    if st.session_state["dd_step"] < 2 and c2.button("Next ➡️", key="dd_nav_next"):
        st.session_state["dd_step"] += 1
        st.rerun()
