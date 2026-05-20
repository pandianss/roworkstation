from __future__ import annotations
import streamlit as st
from src.interface.streamlit.state.services import get_master_service
from src.application.services.communication_service import CommunicationService
from src.infrastructure.persistence.database import get_db_session
from src.interface.streamlit.components.primitives import render_action_bar

def render() -> None:
    user_dept = st.session_state.get("user_dept", "GENERAL ADMIN")
    render_action_bar("RO Coordination Center", [f"Dept: {user_dept}", "Ticketing", "Cross-Unit Support"])
    
    st.markdown("### 📬 Incoming Requests from Branches")
    st.caption(f"Showing active requests for the **{user_dept}** department.")
    
    with get_db_session() as session:
        com_svc = CommunicationService(session)
        requests = com_svc.get_requests_for_dept(user_dept)
        
        if not requests:
            st.info("No requests currently pending for your department.")
            return

        for r in requests:
            status_color = {"PENDING": "gray", "IN_PROGRESS": "blue", "RESOLVED": "green", "CLOSED": "red"}.get(r.status, "black")
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{r.subject}**")
                    st.caption(f"From: SOL {r.sender_unit} ({r.sender_name}) | Sent: {r.created_at.strftime('%d.%m.%Y %H:%M')}")
                    st.write(f"_{r.message}_")
                    
                    if r.response_message:
                        st.markdown(f"**Response:** {r.response_message}")
                
                with c2:
                    st.markdown(f"**Status:** :{status_color}[{r.status}]")
                    st.markdown(f"**Priority:** {r.priority}")
                    
                    if r.status != "RESOLVED":
                        if st.button("📝 Respond", key=f"resp_btn_{r.id}"):
                            st.session_state[f"responding_to_{r.id}"] = True
                
                if st.session_state.get(f"responding_to_{r.id}"):
                    with st.form(f"resp_form_{r.id}"):
                        response = st.text_area("Your Response", value=r.response_message or "")
                        col1, col2 = st.columns(2)
                        if col1.form_submit_button("Submit Response", use_container_width=True):
                            if com_svc.respond_to_request(r.id, response, st.session_state.get("username", "RO User")):
                                st.success("Response sent!")
                                del st.session_state[f"responding_to_{r.id}"]
                                st.rerun()
                        if col2.form_submit_button("Cancel", use_container_width=True):
                            del st.session_state[f"responding_to_{r.id}"]
                            st.rerun()
