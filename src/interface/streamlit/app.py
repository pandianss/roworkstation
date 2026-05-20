from __future__ import annotations

import streamlit as st
import datetime
import getpass

from src.application.services.session_service import SessionService
from src.core.config.config_loader import get_app_settings
from src.core.security.auth import resolve_current_user
from src.interface.streamlit.router import PAGE_REGISTRY, render_page
from src.interface.streamlit.seo import inject_seo_metadata
from src.interface.streamlit.state import ensure_app_state, ensure_filter_state, ensure_user_state
from src.interface.streamlit.theme import apply_theme


# Base64 encoded icons from provided SVG files (White Optimized)
FAVICON_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNDQwIDE0NDAiPjxwYXRoIGZpbGw9IndoaXRlIiBkPSJNNzIwIDIyTDM4NyAzNTZsNDIgNDEgMjkxLTI5MSAyOTIgMjkyIDQxLTQyek03MjAgMTQ3bC0yMSAyMS0yNTAgMjUwIDQyIDQxIDIyOS0yMjkgMjI5IDIyOSA0Mi00MnpNNzIwIDI3MmwtMjEgMjEtMTg3IDE4NyA0MiA0MiAxNjYtMTY3IDE2NyAxNjcgNDItNDJ6TTM2NiAzNzZsLTIxIDIxLTMxMiAzMTMgNDEgNDEgMjkyLTI5MSAyOTIgMjkxIDQxLTQxek0xMDc0IDM3NmwtMjEgMjEtMzEyIDMxMyA0MiA0MSAyOTEtMjkxIDI5MiAyOTEgNDItNDJ6TTM2NiA1MDFsLTIxIDIxLTI1MCAyNTAgNDIgNDIgMjI5LTIyOSAyMjkgMjI5IDQyLTQyek0xMDc0IDUwMWwtMjcxIDI3MSA0MiA0MiAyMjktMjI5IDIyOSAyMjkgNDItNDJ6TTM2NiA2MjZsLTIxIDIxLTE4NyAxODcgNDEgNDIgMTY3LTE2NyAxNjYgMTY3IDQyLTQyek0xMDc0IDYyNmwtMjEgMjEtMTg3IDE4NyA0MiA0MiAxNjYtMTY3IDE2NyAxNjcgNDEtNDJ6bS0xMDYyIDEwNGMwIDI4IDAgNTYgMCA4M0wzNjYgMTE2OGwzMzktMzM5di04NGwtMjcgMjctMzEyIDMxMi0xMDQtMTA0TDU0IDc3MnptMTQxNiAwbC0yMjkgMjI5aDBsLTEyNSAxMjUtMTI1LTEyNS0xODctMTg3LTI3LTI3djgzbDMzOSAzMzkgMzU0LTM1NHptLTE0MTYgMTI1djgzbDM1NCAzNTQgMzM5LTMzOVY4NzBMMzY2IDEyMDl6bTE0MTYgMEwxMDc0IDEyMDlsLTMzOS0zMzl2ODNsMzM5IDMzOSAzNTQtMzU0em0tMTQxNiAxMjV2ODNsMzU0IDM1NCAzMzktMzM5di04M2wtMzM5IDMzOXptMTQxNiAwTDEwNzQgMTMzNGwtMzM5LTMzOXY4M2wzMzkgMzM5IDM1NC0zNTR6Ii8+PC9zdmc+"
LOGO_B64 = FAVICON_B64

def _render_header() -> None:
    display_name = st.session_state.get("display_name", "User")
    st.markdown(
        f"""
        <div class="top-bar-container">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 1.4rem;">👋</span>
                <span style="font-size: 1.1rem; font-weight: 600; color: #ffffff; letter-spacing: 0.5px;">
                    Welcome, {display_name.upper()} 
                    <span style="color: rgba(255,255,255,0.4); margin: 0 12px; font-weight: 300;">|</span> 
                    <span style="color: rgba(255,255,255,0.7); font-weight: 400; font-size: 0.95rem;">Regional Operations Cockpit</span>
                </span>
            </div>
            <div style="font-size: 0.85rem; color: rgba(255,255,255,0.5); font-weight: 500;">
                {datetime.datetime.now().strftime("%A, %d %B %Y")}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def _render_sidebar() -> str:
    from src.core.logging.audit import AuditLogger
    audit_logger = AuditLogger()
    username = st.session_state.get("username", "GUEST")
    is_guest = st.session_state.get("role") == "GUEST"
    
    # We use a session state key to handle clicks from quick access
    if "requested_page" not in st.session_state:
        st.session_state["requested_page"] = "Dashboard"

    if is_guest:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True
        )
        page = st.session_state.get("requested_page", "Guest Portal")
        if "first_view_logged" not in st.session_state:
            audit_logger.log(username, f"Viewed page {page}")
            st.session_state["first_view_logged"] = True
        return page

    # Premium Sidebar Navigation CSS
    st.sidebar.markdown(
        """
        <style>
        /* Modern Sidebar Container */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* 1. GLOBAL LEFT ALIGNMENT (CRITICAL) */
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button * {
            text-align: left !important;
            justify-content: flex-start !important;
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
        }

        /* 2. SECTION HEADERS (The Boxes) */
        .hdr-trigger + div .stButton > button {
            background-color: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            padding: 10px 14px !important;
            color: #f1f5f9 !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            margin-top: 14px !important;
            margin-bottom: 6px !important;
            border-radius: 8px !important;
        }

        /* 3. SUBMENU ITEMS (Pure Links) */
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding-left: 0 !important;
            color: rgba(255, 255, 255, 0.45) !important;
            font-size: 0.85rem !important;
            animation: navSlideDown 0.3s ease-out forwards;
        }
        
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button:hover {
            color: #60a5fa !important;
            text-decoration: underline !important;
            background-color: transparent !important;
        }

        @keyframes navSlideDown {
            from { opacity: 0; transform: translateY(-5px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Quick Access Links */
        div[data-testid="stSidebar"] button[key^="quick_"] {
            background-color: transparent !important;
            border: none !important;
            color: #94a3b8 !important;
            font-size: 0.9rem !important;
            padding: 4px 10px !important;
        }

        /* Tighten vertical spacing */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0px !important;
        }

        /* Scrollbar Styling */
        [data-testid="stSidebar"] ::-webkit-scrollbar { width: 4px; }
        [data-testid="stSidebar"] ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        </style>
        """,
        unsafe_allow_html=True
    )

    is_admin = st.session_state.get("role") == "ADMIN"
    
    if not is_guest:
        st.sidebar.markdown("### 🚀 Quick Access")
        frequent_pages = audit_logger.get_frequent_pages(username)
        if frequent_pages:
            for p in frequent_pages:
                if st.sidebar.button(f"👉 {p}", key=f"quick_{p}", use_container_width=True):
                    st.session_state["requested_page"] = p
                    st.rerun()
        else:
            st.sidebar.caption("No frequent pages yet.")

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🛠️ Workstation Hub")
        
        # Define Groups for logical organization
        navigation_structure = {
        "📊 Insights": ["Dashboard", "MIS", "Campaign Management", "Account Performance"],
        "🏗️ Operations": ["Document Hub", "Coordination Center"],
        "⚖️ Compliance": ["Returns & Compliance"],
        "📂 Library & Archives": ["Policy & Product Archive", "Central Archive"],
        "🌐 Portals": ["Branch Portal", "Guest Portal", "Anniversary Portal"],
        "🛠️ Management": ["Field Guardian", "Branch Visits", "Admin"],
    }

        current_page = st.session_state.get("requested_page", "Dashboard")


        # --- Accordion Navigation Logic ---
        if "active_group" not in st.session_state:
            # Initial determination of active group based on current page
            st.session_state["active_group"] = next((g for g, pgs in navigation_structure.items() if current_page in pgs), "📊 Insights")

        for group, pages in navigation_structure.items():
            allowed_in_group = [p for p in pages if is_admin or p != "Admin"]
            if not allowed_in_group:
                continue
                
            # Inject the CSS trigger before the header button
            st.sidebar.markdown('<div class="hdr-trigger"></div>', unsafe_allow_html=True)
            is_active = st.session_state["active_group"] == group
            header_label = f"{'▼' if is_active else '▶'} {group}"
            
            if st.sidebar.button(header_label, key=f"hdr_{group}", use_container_width=True):
                st.session_state["active_group"] = group if not is_active else None
                st.rerun()

            # Render children only if this group is active (The Accordion effect)
            if is_active:
                # Wrap submenus in an animated container
                st.sidebar.markdown('<div class="submenu-container">', unsafe_allow_html=True)
                for p in allowed_in_group:
                    # Physical Indent via columns
                    col_indent, col_btn = st.sidebar.columns([0.1, 0.9])
                    with col_btn:
                        if st.button(p, key=f"nav_btn_{p}", use_container_width=True):
                            if p != current_page:
                                st.session_state["requested_page"] = p
                                st.session_state["active_group"] = group
                                audit_logger.log(username, f"Viewed page {p}")
                                st.rerun()
                st.sidebar.markdown('</div>', unsafe_allow_html=True)

    page = st.session_state["requested_page"]
    
    # Log initial view if not already logged for this session's first run
    if "first_view_logged" not in st.session_state:
        audit_logger.log(username, f"Viewed page {page}")
        st.session_state["first_view_logged"] = True
    
    # Admin Password Override Section
    if not is_admin:
        st.sidebar.markdown("---")
        with st.sidebar.expander("🔐 Unlock Admin Access"):
            with st.form("admin_upgrade_form"):
                admin_pass = st.text_input("Admin Password", type="password")
                if st.form_submit_button("Elevate Privileges", use_container_width=True):
                    import time
                    if "admin_failed_attempts" not in st.session_state:
                        st.session_state.admin_failed_attempts = 0
                    if "admin_lockout_time" not in st.session_state:
                        st.session_state.admin_lockout_time = 0

                    if time.time() < st.session_state.admin_lockout_time:
                        st.error(f"Account locked. Try again in {int(st.session_state.admin_lockout_time - time.time())} seconds.")
                    else:
                        settings = get_app_settings()
                        if admin_pass == settings.admin_password:
                            st.session_state.admin_failed_attempts = 0
                            st.session_state.admin_lockout_time = 0
                            SessionService().start_session(username)
                            st.success("Admin access granted!")
                            st.rerun()
                        else:
                            st.session_state.admin_failed_attempts += 1
                            if st.session_state.admin_failed_attempts >= 5:
                                st.session_state.admin_lockout_time = time.time() + 300
                                st.error("Account locked for 5 minutes due to too many failed attempts.")
                            else:
                                st.error("Invalid password")


    # Role Toggle for Admins
    if st.session_state.get("original_role") == "ADMIN" or st.session_state.get("is_elevated"):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### View Mode")
        new_role = st.sidebar.toggle("Admin Mode", value=(st.session_state["role"] == "ADMIN"))
        target_role = "ADMIN" if new_role else "USER"
        
        if target_role != st.session_state["role"]:
            st.session_state["role"] = target_role
            st.rerun()

    # --- System Controls ---
    if not is_guest:
        st.sidebar.markdown("---")
        with st.sidebar.expander("🛠️ System & Data", expanded=False):
            if st.button("🔄 Sync Master Data", key="sync_masters_btn", use_container_width=True, help="Update database from Staff and Branch CSV files."):
                from src.application.services.master_service import MasterService
                with st.spinner("Synchronizing..."):
                    MasterService().sync_if_needed()
                st.success("Master records updated!")
                st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("This interface is backed by the new layered architecture.")
    return page


def _require_login() -> bool:
    current_user = resolve_current_user()

    st.session_state["username"] = current_user.username
    st.session_state["role"] = current_user.role
    st.session_state["user_dept"] = current_user.dept
    st.session_state["user_depts"] = current_user.depts

    if current_user.role == "GUEST" and "requested_page" not in st.session_state:
        st.session_state["requested_page"] = "Guest Portal"
        st.session_state["active_group"] = "🌐 Portals"

    return True


def run() -> None:
    settings = get_app_settings()
    favicon_uri = f"data:image/svg+xml;base64,{FAVICON_B64}"
    st.set_page_config(page_title=settings.app_title, page_icon=favicon_uri, layout="wide")
    
    # Bulletproof URL guard: prevent any query parameter injection
    st.query_params.clear()
    
    inject_seo_metadata(settings)
    ensure_app_state()
    ensure_filter_state()
    apply_theme()
    if not _require_login():
        st.stop()
    ensure_user_state()
    
    # Auto-Sync once on startup if never synced or files changed
    if "initial_sync_done" not in st.session_state:
        from src.application.services.master_service import MasterService
        MasterService().sync_if_needed()
        st.session_state["initial_sync_done"] = True
    
    _render_header()
    page = _render_sidebar()
    from src.interface.streamlit.state.app_state import cleanup_stale_session_assets
    cleanup_stale_session_assets(page)
    render_page(page)
