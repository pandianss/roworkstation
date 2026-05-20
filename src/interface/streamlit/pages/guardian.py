from __future__ import annotations

import datetime
import pandas as pd
import streamlit as st

from src.application.services.admin_service import AdminService
from src.application.services.guardian_service import GuardianService
from src.application.services.document.service import DocumentService
from src.interface.streamlit.components.primitives import render_action_bar, render_data_table


def render() -> None:
    admin_service = AdminService()
    guardian_service = GuardianService()
    doc_service = DocumentService()
    
    render_action_bar("Guardian", ["Field follow-ups", "Regional requests", "Activity feed"])
    
    st.markdown("## 🛡️ Guardian Operations Portal")
    st.caption("Central RO-to-Branch collaborative workspace with portfolio MIS, daily task board, structured updates, and daily briefing compilations.")

    # 1. Resolve logged-in User and Assigned Portfolio
    username = st.session_state.get("username", "admin")
    user = admin_service.get_user(username)
    is_admin = user.role == "ADMIN" if user else False
    user_dept = st.session_state.get("user_dept", "ALL") if user else "ALL"
    is_planning_officer = is_admin or user_dept.upper() == "PLANNING" or "PLANNING" in username.upper()
    
    from src.interface.streamlit.state.services import get_master_service
    master_svc = get_master_service()
    
    all_staff_users = admin_service.list_users()
    ro_staff_sols = {s.code for s in master_svc.get_by_category("STAFF") if str(s.metadata.get("sol")) == "3933"}
    ro_staff_sols.add("admin")
    ro_staff_users = [u for u in all_staff_users if u.username in ro_staff_sols]

    # Portfolio Assignment Board for Planning Officers / Admins
    if is_planning_officer:
        with st.expander("🛡️ Administrative: Assign Guardian Portfolios", expanded=False):
            st.markdown("##### Assign Multiple Branch Portfolios to Guardian Officers")
            st.caption("Select any RO Staff member and select the branch SOLs to assign to their field portfolio.")
            
            staff_options = sorted([u.username for u in ro_staff_users])
            
            def format_staff_opt(u_code):
                s = next((u for u in ro_staff_users if u.username == u_code), None)
                return f"{u_code} - {s.name} ({s.designation or 'Staff'})" if s else u_code

            all_units = master_svc.get_by_category("UNIT")
            branch_options = sorted([str(u.code) for u in all_units if u.code != "3933"])
            
            def format_branch_opt(sol_code):
                b = next((u for u in all_units if str(u.code) == sol_code), None)
                return f"SOL {sol_code} - {b.name_en}" if b else f"SOL {sol_code}"

            with st.form("portfolio_assignment_form"):
                target_officer = st.selectbox("Select Guardian Officer", options=staff_options, format_func=format_staff_opt)
                
                selected_officer_obj = next((u for u in ro_staff_users if u.username == target_officer), None)
                current_assigned = selected_officer_obj.assigned_branches if selected_officer_obj else []
                current_assigned = [str(s) for s in current_assigned if str(s) in branch_options]
                
                new_assigned = st.multiselect(
                    "Assign Portfolios (Select Multiple)",
                    options=branch_options,
                    default=current_assigned,
                    format_func=format_branch_opt
                )
                
                submit_assign = st.form_submit_button("💾 Save Portfolio Assignments", type="primary", use_container_width=True)
                
            if submit_assign:
                admin_service.assign_branches_to_user(target_officer, new_assigned)
                st.cache_data.clear()
                st.success(f"Successfully updated branch portfolio for {format_staff_opt(target_officer)}!")
                st.rerun()

            # Render a high-density current assignments inventory table
            import pandas as pd
            inventory_records = []
            for ro_user in ro_staff_users:
                if ro_user.username == "admin":
                    continue
                branches = ro_user.assigned_branches
                branches_formatted = ", ".join(sorted(branches)) if branches else "—"
                inventory_records.append({
                    "Staff Code": ro_user.username,
                    "Name": ro_user.name or "N/A",
                    "Designation": ro_user.designation or "Executive",
                    "Assigned Branch SOLs": branches_formatted
                })
            
            if inventory_records:
                st.markdown("---")
                st.markdown("##### 📋 Live Portfolio Assignments Directory")
                inv_df = pd.DataFrame(inventory_records)
                st.dataframe(inv_df, use_container_width=True, hide_index=True)

    assigned_sols = user.assigned_branches if user else []
    if not assigned_sols or "ALL" in assigned_sols or is_admin:
        all_units = master_svc.get_by_category("UNIT")
        assigned_sols = [str(u.code) for u in all_units if u.code != "3933"]
    
    # 2. Setup Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Portfolio Cockpit",
        "📢 Daily Directives Board",
        "📝 Follow-Up Journal",
        "📋 Executive Daily Digest"
    ])

    # ----------------------------------------------------
    # TAB 1: Portfolio Cockpit
    # ----------------------------------------------------
    with tab1:
        st.markdown("### 📊 Portfolio Performance Snashot")
        st.caption(f"Currently viewing latest MIS metrics for your {len(assigned_sols)} assigned branch(es).")
        
        portfolio_data = guardian_service.get_portfolio_mis(assigned_sols)
        if portfolio_data:
            p_df = pd.DataFrame(portfolio_data)
            
            # Format and render KPI tiles
            total_adv = p_df["advances"].sum()
            total_dep = p_df["deposits"].sum()
            avg_cd = p_df["cd_ratio"].mean()
            avg_casa = p_df["casa_ratio"].mean()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Portfolio Advances", f"₹ {total_adv:.2f} Cr")
            col2.metric("Portfolio Deposits", f"₹ {total_dep:.2f} Cr")
            col3.metric("Avg CD Ratio", f"{avg_cd:.2f} %")
            col4.metric("Avg CASA Ratio", f"{avg_casa:.2f} %")
            
            st.markdown("#### Portfolio Detail Inventory")
            # Present high-density data table
            display_df = p_df.copy()
            display_df.columns = [c.upper().replace("_", " ") for c in display_df.columns]
            render_data_table(display_df, "Portfolio Branches Performance", "portfolio_branches.xlsx")
        else:
            st.info("No active performance records found for your tagged branch portfolio. Ensure MIS spreadsheets have been uploaded.")

    # ----------------------------------------------------
    # TAB 2: Daily Directives Board
    # ----------------------------------------------------
    with tab2:
        st.markdown("### 📢 Collaborative Daily Operations Focus")
        st.caption("Aggregated daily action priorities and directives shared by Regional Office Guardian Officers.")
        
        # Today's Date String
        today_str = datetime.date.today().strftime("%d.%m.%Y")
        
        # Form to add focus directive
        with st.expander("➕ Post New Focus Directive for Today", expanded=False):
            with st.form("new_directive_form"):
                d_title = st.text_input("Directive Title/Focus Area", placeholder="e.g., Target CASA Drive / Gold Loan renewals")
                d_desc = st.text_area("Detailed Operational Instructions", placeholder="Describe the focus instructions or follow-up milestones for today...")
                submit_d = st.form_submit_button("Post Directive")
            
            if submit_d:
                if d_title.strip() and d_desc.strip():
                    guardian_service.create_daily_task(username, d_title.strip(), d_desc.strip())
                    st.success("Shared directive posted successfully!")
                else:
                    st.warning("Please fill in both the title and instructions.")
        
        # Display today's directives
        st.markdown("#### Active Directives for Today")
        today_tasks = guardian_service.list_daily_tasks(today_str)
        if today_tasks:
            for task in today_tasks:
                st.markdown(
                    f"""
                    <div style="padding: 12px 15px; border-left: 5px solid #254aa0; background-color: #f8fafc; border-radius: 0 5px 5px 0; margin-bottom: 12px;">
                        <span style="font-size: 8.5pt; font-weight: bold; color: #254aa0; background-color: #e0e7ff; padding: 2px 6px; border-radius: 3px; float: right;">Posted by: {task.posted_by}</span>
                        <h5 style="margin: 0 0 5px 0; color: #1e293b; font-size: 11pt;">{task.title}</h5>
                        <p style="margin: 0; color: #475569; font-size: 9.5pt; white-space: pre-line;">{task.description}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No focus directives posted for today yet.")

    # ----------------------------------------------------
    # TAB 3: Follow-Up Journal
    # ----------------------------------------------------
    with tab3:
        st.markdown("### 📝 Structured Follow-Up Journal")
        st.caption("Record structured observations and follow-up activities for your portfolio branches.")
        
        # Today's active directives for ready reference
        today_directives = guardian_service.list_daily_tasks(today_str)
        if today_directives:
            with st.expander(f"📢 Active Daily Directives ({len(today_directives)}) — RO Follow-Up Focus", expanded=True):
                for task in today_directives:
                    st.markdown(
                        f"""
                        <div style="padding: 10px 12px; border-left: 4px solid #254aa0; background-color: #f8fafc; border-radius: 0 4px 4px 0; margin-bottom: 8px;">
                            <span style="font-size: 8pt; font-weight: bold; color: #254aa0; background-color: #e0e7ff; padding: 1px 5px; border-radius: 2px; float: right;">By: {task.posted_by}</span>
                            <h6 style="margin: 0 0 3px 0; color: #1e293b; font-size: 9.5pt;">{task.title}</h6>
                            <p style="margin: 0; color: #475569; font-size: 9pt; white-space: pre-line;">{task.description}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        # Branch Selection Dropdown
        selected_unit_code = st.selectbox(
            "Select Branch to Follow-Up",
            options=assigned_sols,
            format_func=lambda s: f"SOL {s} - {master_svc.get_by_category('UNIT')}" if False else f"SOL {s}"
        )
        
        # Form to add follow-up log
        with st.form("structured_followup_form"):
            col_f1, col_f2 = st.columns(2)
            f_cat = col_f1.selectbox("Business Category", ["CASA Mobilization", "NPA Recovery", "Gold Loan Growth", "Audit & Cleanliness", "Other"])
            f_priority = col_f2.selectbox("Action Priority", ["P1 (Critical)", "P2 (High)", "P3 (Normal)", "P4 (Low)"])
            f_status = st.selectbox("Current Progress State", ["PENDING_BRANCH", "RESOLVED", "ESCALATED_RO"])
            f_details = st.text_area("Detailed Action Details & Follow-up observations", placeholder="State follow-up details (e.g., manager committed to recovery targets, active steps taken, staff constraint observations)...")
            submit_f = st.form_submit_button("Record Observation")
            
        if submit_f:
            if f_details.strip() and selected_unit_code:
                priority_val = f_priority.split()[0] # e.g. "P1"
                guardian_service.record_followup(
                    go_username=username,
                    sol=selected_unit_code,
                    details=f_details.strip(),
                    category=f_cat,
                    status=f_status,
                    priority=priority_val
                )
                st.success(f"Follow-up for SOL {selected_unit_code} successfully logged!")
            else:
                st.warning("Please enter detailed follow-up observations.")
                
        # Display branch history
        st.markdown(f"#### Follow-Up History for SOL {selected_unit_code}")
        unit_followups = guardian_service.list_followups(sol=selected_unit_code)
        if unit_followups:
            # Sort by timestamp descending
            sorted_f = sorted(unit_followups, key=lambda f: f.timestamp, reverse=True)
            for item in sorted_f:
                ts_str = item.timestamp.strftime("%d-%b-%Y %I:%M %p") if hasattr(item.timestamp, "strftime") else str(item.timestamp)
                st.markdown(
                    f"""
                    <div style="padding: 10px 15px; border-bottom: 1px solid #f1f5f9;">
                        <span style="font-size: 8pt; color: #94a3b8; float: right;">{ts_str}</span>
                        <strong>{item.go_username}</strong> logged a 
                        <span style="background-color:#f1f5f9; padding: 2px 5px; border-radius: 3px; font-size: 8pt;">{item.category}</span> observation:
                        <p style="margin: 5px 0 0 0; color: #475569; font-size: 9.5pt; white-space: pre-line;">{item.details}</p>
                        <div style="margin-top: 5px; font-size: 8pt;">
                            Priority: <strong style="color:#e11d48;">{item.priority}</strong> &bull; 
                            Status: <strong style="color:#2563eb;">{item.status}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info(f"No previous follow-up records logged for SOL {selected_unit_code}.")

    # ----------------------------------------------------
    # TAB 4: Executive Daily Digest
    # ----------------------------------------------------
    with tab4:
        st.markdown("### 📋 Executive Daily Digest Memo")
        st.caption("Generate and download the single aggregated operational memo (1 document per day) summarizing all RO directives and branch follow-ups.")
        
        # Report Date Input
        selected_rep_date = st.date_input("Select Report Date", datetime.date.today())
        rep_date_str = selected_rep_date.strftime("%d.%m.%Y")
        
        # Resolve initiator (logged-in user) details
        curr_user_obj = next((u for u in all_staff_users if u.username == username), None)
        if curr_user_obj:
            curr_name = curr_user_obj.name
            curr_desig = curr_user_obj.designation or "Guardian Officer"
            default_compiled_by = f"{curr_name} ({curr_desig})"
        else:
            default_compiled_by = f"{username} (Guardian Officer)"
            
        # Compile RO executives options list (SOL 3933)
        ro_executives_opts = sorted([
            f"{u.name} ({u.designation or 'Officer'})"
            for u in ro_staff_users if u.username != "admin"
        ])
        if not ro_executives_opts:
            ro_executives_opts = ["Assistant General Manager", "Chief Regional Manager"]
            
        # Detect sensible default indices & list of values
        default_review_vals = []
        for opt in ro_executives_opts:
            if any(term in opt.upper() for term in ["AGM", "ASSISTANT GENERAL", "CHIEF MANAGER"]):
                default_review_vals.append(opt)
        if not default_review_vals and ro_executives_opts:
            default_review_vals = [ro_executives_opts[0]]
            
        def_approve_idx = min(1, len(ro_executives_opts) - 1) if len(ro_executives_opts) > 1 else 0
        for idx, opt in enumerate(ro_executives_opts):
            if any(term in opt.upper() for term in ["SRM", "SENIOR REGIONAL", "CHIEF REGIONAL", "REGIONAL MANAGER"]):
                def_approve_idx = idx
                break

        # Signatory Configurator
        with st.expander("✍️ Signatory Configuration", expanded=True):
            col_s1, col_s2, col_s3 = st.columns(3)
            sig_compile = col_s1.text_input("Compiled By (Initiator)", value=default_compiled_by)
            sig_review = col_s2.multiselect("Reviewed By (Multiple Allowed)", options=ro_executives_opts, default=default_review_vals)
            sig_approve = col_s3.selectbox("Approved By", options=ro_executives_opts, index=def_approve_idx)
        
        # Pull Compiled Report data
        report_data = guardian_service.compile_daily_report(rep_date_str)
        
        # Render dynamic buttons
        col_r1, col_r2 = st.columns(2)
        
        # Direct Download of PDF
        pdf_bytes = None
        if col_r1.button("Compile & Download PDF Briefing Note", use_container_width=True, type="primary"):
            with st.spinner("Compiling trilingual daily operations digest..."):
                try:
                    pdf_bytes = doc_service.generate_daily_guardian_digest_pdf(rep_date_str, sig_compile, sig_review, sig_approve)
                    st.download_button(
                        label="💾 Download Daily Briefing Note (PDF)",
                        data=pdf_bytes,
                        file_name=f"RO_Daily_Guardian_Digest_{rep_date_str.replace('.', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as ex:
                    st.error(f"Failed to compile PDF: {ex}")
                    
        # View HTML Preview
        if col_r2.button("Generate Live HTML Preview", use_container_width=True):
            with st.spinner("Generating preview..."):
                try:
                    html_content = doc_service.generate_daily_guardian_digest_html(rep_date_str, sig_compile, sig_review, sig_approve)
                    st.components.v1.html(html_content, height=800, scrolling=True)
                except Exception as ex:
                    st.error(f"Failed to generate HTML preview: {ex}")

        # Show a summary count of compiled items
        st.markdown("---")
        st.markdown(f"#### Summary for Date: `{rep_date_str}`")
        s_col1, s_col2 = st.columns(2)
        s_col1.metric("Shared Directives Posted", len(report_data["directives"]))
        s_col2.metric("Branch Follow-ups Recorded", len(report_data["followups"]))
