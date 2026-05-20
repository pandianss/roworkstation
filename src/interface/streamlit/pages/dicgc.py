from __future__ import annotations

import datetime
import streamlit as st
import pandas as pd
from src.application.services.document import DocumentService
from src.application.services.dicgc_service import DICGCService
from src.infrastructure.persistence.database import get_db_session
from src.interface.streamlit.components.primitives import render_action_bar
from src.core.utils.number_utils import format_indian_number

def render() -> None:
    render_action_bar("DICGC Half-Yearly Return Wizard", ["Form DI-01", "Premium Assessment", "Deposit Breakup"])

    if "dicgc_step" not in st.session_state:
        st.session_state["dicgc_step"] = 1
    
    if "dicgc_data" not in st.session_state:
        st.session_state["dicgc_data"] = {
            "bank_code": "630",
            "bank_name_address": "Indian Overseas Bank, Regional Office, 80 Feet Road, Dindigul - 624001",
            "half_year_ending": datetime.date(2026, 3, 31),
            "total_deposits": 0.0,
            "foreign_govt_deposits": 0.0,
            "central_govt_deposits": 0.0,
            "state_govt_deposits": 0.0,
            "inter_bank_deposits": 0.0,
            "exempted_deposits": 0.0,
            "other_balances": 0.0,
            "assessable_deposits": 0.0,
            # Items 4-12
            "sundry_creditors": 0.0,
            "unpaid_dds": 0.0,
            "local_authorities": 0.0,
            "autonomous_bodies": 0.0,
            "security_deposits_govt": 0.0,
            "govt_embassy_officials": 0.0,
            "overdue_unclaimed": 0.0,
            "interest_accrued_payable": 0.0,
            "interest_accrued_all": 0.0,
            # Premium & Tax
            "premium_payable": 0.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 0.0,
            "penal_interest": 0.0,
            "credit_adjustment": 0.0,
            "debit_adjustment": 0.0,
            "penal_interest_debit": 0.0,
            "gst_debit_adjustment": 0.0,
            "breakup": {"n1": 0, "a1": 0.0, "n2": 0, "a2": 0.0, "n3": 0, "a3": 0.0, "n4": 0, "a4": 0.0},
            "sundry_summary": {
                "clearing_diff": 0.0,
                "clearing_next": 0.0,
                "deposits": 0.0,
                "claims": 0.0,
                "suit_filed": 0.0,
                "it_st_attach": 0.0,
                "tds": 0.0,
                "excess_cash": 0.0,
                "vigilance": 0.0,
                "others": 0.0,
                "total": 0.0
            },
            "last_half_year_assessable": 0.0,
            "reason_for_decrease": "",
            "utr_no": "",
            "payment_date": datetime.date.today(),
            "place": "Dindigul",
            "report_date": datetime.date.today(),
            "first_auth_name": "",
            "first_auth_desig": "Regional Manager",
            "second_auth_name": "",
            "second_auth_desig": "Chief Manager"
        }
    
    # Defensive check: ensure breakup exists (prevents UndefinedError if it was popped in a previous session)
    if "breakup" not in st.session_state["dicgc_data"]:
        st.session_state["dicgc_data"]["breakup"] = {"n1": 0, "a1": 0.0, "n2": 0, "a2": 0.0, "n3": 0, "a3": 0.0, "n4": 0, "a4": 0.0}
    
    if "sundry_summary" not in st.session_state["dicgc_data"]:
        st.session_state["dicgc_data"]["sundry_summary"] = {
            "clearing_diff": 0.0, "clearing_next": 0.0, "deposits": 0.0, "claims": 0.0, 
            "suit_filed": 0.0, "it_st_attach": 0.0, "tds": 0.0, "excess_cash": 0.0, 
            "vigilance": 0.0, "others": 0.0, "total": 0.0
        }

    data = st.session_state["dicgc_data"]
    
    # Sidebar Progress
    st.sidebar.markdown("### Progress")
    steps = [
        "1. Bank & Period",
        "2. Total Deposits (Item 1)",
        "3. Exclusions (1a-1e)",
        "4. Other balances (Item 2 & 3)",
        "5. Sundry & DDs (Item 4 & 5)",
        "6. Format-I: Sundry Summary",
        "7. Other items (Item 6-12)",
        "8. Break-up (Item 13)",
        "9. Review & Export"
    ]
    for i, s in enumerate(steps):
        if st.session_state["dicgc_step"] == i + 1:
            st.sidebar.info(f"**{s}**")
        elif st.session_state["dicgc_step"] > i + 1:
            st.sidebar.success(f"{s} (Done)")
        else:
            st.sidebar.text(s)

    # STEP 1: Bank & Period
    if st.session_state["dicgc_step"] == 1:
        st.markdown("### 🏦 Step 1: Bank & Period Information")
        col1, col2 = st.columns(2)
        with col1:
            data["bank_code"] = st.text_input("Insured Bank Code / Registration No.", value=data["bank_code"])
            data["half_year_ending"] = st.date_input("Half Year ending on", value=data["half_year_ending"])
        with col2:
            data["bank_name_address"] = st.text_area("Bank's Name and Address", value=data["bank_name_address"])
            
    # STEP 2: Total Deposits (Item 1)
    elif st.session_state["dicgc_step"] == 2:
        st.markdown("### 💰 Step 2: Item 1 — Total Deposits")
        st.caption("All amounts in Rs. '000 (thousands)")
        data["total_deposits"] = st.number_input("Total Deposits at close of business", value=data["total_deposits"], step=1.0)

    # STEP 3: Exclusions (1a to 1e)
    elif st.session_state["dicgc_step"] == 3:
        st.markdown("### 🛡️ Step 3: Items 1(a)–1(e) — Excluded Categories")
        st.caption("All amounts in Rs. '000 (thousands)")
        with st.container():
            data["foreign_govt_deposits"] = st.number_input("(a) Deposits of Foreign Governments", value=data["foreign_govt_deposits"], step=1.0)
            data["central_govt_deposits"] = st.number_input("(b) Deposits of Central Government", value=data["central_govt_deposits"], step=1.0)
            data["state_govt_deposits"] = st.number_input("(c) Deposits of State Government", value=data["state_govt_deposits"], step=1.0)
            data["inter_bank_deposits"] = st.number_input("(d) Inter Bank Deposits", value=data["inter_bank_deposits"], step=1.0)
            data["exempted_deposits"] = st.number_input("(e) Specifically exempted by DICGC", value=data["exempted_deposits"], step=1.0)

    # STEP 4: Other balances (Item 2 & 3)
    elif st.session_state["dicgc_step"] == 4:
        st.markdown("### 📊 Step 4: Item 2 — Other Balances")
        st.caption("All amounts in Rs. '000 (thousands)")
        data["other_balances"] = st.number_input("Any other balance due to depositor not clubbed under 'Deposits' at Item 1", value=data["other_balances"], step=1.0)
        
        # Calculation
        exclusions = data["foreign_govt_deposits"] + data["central_govt_deposits"] + data["state_govt_deposits"] + data["inter_bank_deposits"] + data["exempted_deposits"]
        assessable = data["total_deposits"] - exclusions + data["other_balances"]
        data["assessable_deposits"] = assessable
        
        st.metric("Item 3 — Assessable Deposits (Calculated)", f"Rs. {format_indian_number(assessable, decimals=0)} ('000)")
        st.info("Formula: Item 1 − (1a+1b+1c+1d+1e) + Item 2")

    # STEP 5: Sundry & DDs (Item 4 & 5)
    elif st.session_state["dicgc_step"] == 5:
        st.markdown("### 📑 Step 5: Items 4 & 5 — Sundry Creditors & DDs")
        st.caption("All amounts in Rs. '000 (thousands)")
        data["sundry_creditors"] = st.number_input("4. Amount relating to deposit held in Sundry Creditors A/c", value=data["sundry_creditors"], step=1.0)
        data["unpaid_dds"] = st.number_input("5. Unpaid Demand Drafts issued by closing deposit accounts", value=data["unpaid_dds"], step=1.0)

    # STEP 6: Format-I (Sundry Summary)
    elif st.session_state["dicgc_step"] == 6:
        st.markdown("### 📋 Step 6: Format-I — Sundry Creditors Summary")
        st.caption("Consolidated figures for the Region. Amounts in Rupees (not '000)")
        
        s = data["sundry_summary"]
        col1, col2 = st.columns(2)
        with col1:
            s["clearing_diff"] = st.number_input("CLEARING DIFFERENCE", value=s["clearing_diff"], step=1.0)
            s["clearing_next"] = st.number_input("CLEARING NEXT DAY", value=s["clearing_next"], step=1.0)
            s["deposits"] = st.number_input("DEPOSITS", value=s["deposits"], step=1.0)
            s["claims"] = st.number_input("ECGC/DICGC CLAIMS", value=s["claims"], step=1.0)
            s["suit_filed"] = st.number_input("SUIT FILED/COURT", value=s["suit_filed"], step=1.0)
        with col2:
            s["it_st_attach"] = st.number_input("IT/ST ATTACHMENT", value=s["it_st_attach"], step=1.0)
            s["tds"] = st.number_input("TAX DEDUCTED AT SOURCE", value=s["tds"], step=1.0)
            s["excess_cash"] = st.number_input("EXCESS CASH", value=s["excess_cash"], step=1.0)
            s["vigilance"] = st.number_input("VIGILANCE CASES", value=s["vigilance"], step=1.0)
            s["others"] = st.number_input("OTHERS", value=s["others"], step=1.0)
            
        s["total"] = (s["clearing_diff"] + s["clearing_next"] + s["deposits"] + s["claims"] + 
                     s["suit_filed"] + s["it_st_attach"] + s["tds"] + s["excess_cash"] + 
                     s["vigilance"] + s["others"])
        
        st.metric("Total Format-I Summary", f"Rs. {format_indian_number(s['total'])}")
        st.warning("Note: Ensure 'Others' category does not include TDS or any other specific category.")
        
        # Validation with Item 4
        item4_in_rs = data["sundry_creditors"] * 1000
        diff = s["total"] - item4_in_rs
        if abs(diff) < 1.0:
            st.success("Tally Match with Item 4 (Sundry Creditors)!")
        else:
            st.error(f"Mismatch with Item 4: Rs. {format_indian_number(diff)}")

    # STEP 7: Other items (Items 6-12)
    elif st.session_state["dicgc_step"] == 7:
        st.markdown("### 🔍 Step 6: Items 6–12 — Other Reportable Items")
        st.caption("All amounts in Rs. '000 (thousands)")
        data["local_authorities"] = st.number_input("6. Deposits of Local Authorities & quasi-Govt. bodies", value=data["local_authorities"], step=1.0)
        data["autonomous_bodies"] = st.number_input("7. Deposits of autonomous/statutory bodies, Govt. companies", value=data["autonomous_bodies"], step=1.0)
        data["security_deposits_govt"] = st.number_input("8. Security Deposits & Earnest monies held for Govt. Depts.", value=data["security_deposits_govt"], step=1.0)
        data["govt_embassy_officials"] = st.number_input("9. Deposits held in individual names of Govt./Embassy Officials", value=data["govt_embassy_officials"], step=1.0)
        data["overdue_unclaimed"] = st.number_input("10. Overdue Term Deposits & Unclaimed Deposits", value=data["overdue_unclaimed"], step=1.0)
        data["interest_accrued_payable"] = st.number_input("11. Amount of Interest Accrued and Payable", value=data["interest_accrued_payable"], step=1.0)
        data["interest_accrued_all"] = st.number_input("12. Amount of Interest Accrued on all deposits", value=data["interest_accrued_all"], step=1.0)

    # STEP 8: Breakup
    elif st.session_state["dicgc_step"] == 8:
        st.markdown("### 📈 Step 7: Item 13 — Break-up of Assessable Deposits")
        st.info(f"Total assessable deposits to match: Rs. {format_indian_number(data['assessable_deposits'], decimals=0)} ('000)")
        
        b = data["breakup"]
        col1, col2 = st.columns(2)
        with col1:
            b["n1"] = st.number_input("(i) Up to Rs. 5L (Accounts)", value=b["n1"], step=1)
            b["a1"] = st.number_input("(i) Up to Rs. 5L (Amount '000)", value=b["a1"], step=1.0)
            st.divider()
            b["n2"] = st.number_input("(ii) Over 5L up to 7.5L (Accounts)", value=b["n2"], step=1)
            b["a2"] = st.number_input("(ii) Over 5L up to 7.5L (Amount '000)", value=b["a2"], step=1.0)
        with col2:
            b["n3"] = st.number_input("(iii) Over 7.5L up to 10L (Accounts)", value=b["n3"], step=1)
            b["a3"] = st.number_input("(iii) Over 7.5L up to 10L (Amount '000)", value=b["a3"], step=1.0)
            st.divider()
            b["n4"] = st.number_input("(iv) Over 10L (Accounts)", value=b["n4"], step=1)
            b["a4"] = st.number_input("(iv) Over 10L (Amount '000)", value=b["a4"], step=1.0)
            
        breakup_total = b["a1"] + b["a2"] + b["a3"] + b["a4"]
        b["n_total"] = b["n1"] + b["n2"] + b["n3"] + b["n4"]
        b["a_total"] = breakup_total
        
        diff = breakup_total - data["assessable_deposits"]
        if abs(diff) < 0.01:
            st.success(f"Tally Match! Total: Rs. {format_indian_number(breakup_total, decimals=0)} ('000)")
        else:
            st.error(f"Mismatch: Rs. {format_indian_number(diff, decimals=0)} ('000). Total: Rs. {format_indian_number(breakup_total, decimals=0)}")

    # STEP 9: Preview & Export
    elif st.session_state["dicgc_step"] == 9:
        st.markdown("### 📄 Step 8: Preview & Export")
        
        # Calculate Premium & GST for display
        with get_db_session() as session:
            svc = DICGCService(session)
            calcs = svc.calculate_premium(data["assessable_deposits"])
            data["premium_payable"] = calcs["premium"]
            data["cgst"] = calcs["cgst"]
            data["sgst"] = calcs["sgst"]
            data["net_amount_payable"] = calcs["total_payable"]

        with st.expander("Review Final Data", expanded=True):
            st.json(data)
            
        if st.button("🚀 Generate Official Form DI-01", use_container_width=True):
            with st.spinner("Preparing high-fidelity PDF..."):
                doc_service = DocumentService()
                # Prepare data for template
                render_data = data.copy()
                render_data["half_year_ending"] = data["half_year_ending"].strftime("%d.%m.%Y")
                render_data["report_date"] = data["report_date"].strftime("%d.%m.%Y")
                render_data["payment_date"] = data["payment_date"].strftime("%d.%m.%Y")
                
                pdf_bytes = doc_service.generate_dicgc_form_di01(render_data)
                st.session_state["dicgc_pdf"] = pdf_bytes
                st.success("Form DI-01 generated successfully!")
                
                # Also save to DB
                with get_db_session() as session:
                    svc = DICGCService(session)
                    svc.save_return(data)
                    st.info("Record saved to database.")

        if "dicgc_pdf" in st.session_state:
            st.download_button(
                label="📥 Download Official Form DI-01 (PDF)",
                data=st.session_state["dicgc_pdf"],
                file_name=f"DICGC_Form_DI01_{data['half_year_ending'].strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    # Navigation Buttons
    st.divider()
    col_prev, col_next = st.columns([1, 1])
    if st.session_state["dicgc_step"] > 1:
        if col_prev.button("⬅️ Previous"):
            st.session_state["dicgc_step"] -= 1
            st.rerun()
    if st.session_state["dicgc_step"] < 9:
        if col_next.button("Next ➡️"):
            st.session_state["dicgc_step"] += 1
            st.rerun()
            
    st.divider()
    st.caption("This wizard is designed to match the official DICGC Form DI-01 format.")
