from __future__ import annotations
import streamlit as st
import pandas as pd
from src.core.config.config_loader import get_app_settings

def clean_html(s: str) -> str:
    return "".join(line.strip() for line in s.splitlines())

def render_org_chart(master_service) -> None:
    """Renders a beautiful, high-density, interactive Organizational Chart for Dindigul Region."""
    st.markdown(clean_html("""
        <style>
        .org-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            margin: 20px 0;
            width: 100%;
        }
        
        .org-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 18px 24px !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -4px rgba(0, 0, 0, 0.3) !important;
            text-align: center;
            width: 320px;
            transition: all 0.3s ease;
        }
        
        .org-card:hover {
            transform: translateY(-4px);
            border-color: #3b82f6 !important;
            box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.2) !important;
        }
        
        .org-leader-card {
            border: 2px solid #fbbf24 !important;
        }
        
        .org-leader-card:hover {
            border-color: #f59e0b !important;
            box-shadow: 0 20px 25px -5px rgba(245, 158, 11, 0.25) !important;
        }
        
        .org-badge {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #3b82f6;
            margin-bottom: 6px;
        }
        
        .org-leader-badge {
            color: #fbbf24;
        }
        
        .org-name {
            font-size: 1.2rem;
            font-weight: 700;
            color: #ffffff;
            margin: 4px 0;
        }
        
        .org-title {
            font-size: 0.85rem;
            color: #94a3b8;
            font-weight: 500;
        }
        
        .org-contact {
            font-size: 0.8rem;
            color: #10b981;
            font-weight: 600;
            margin-top: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        
        .org-connector {
            width: 2px;
            height: 24px;
            background-color: rgba(255, 255, 255, 0.15);
        }
        
        .org-branch-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            width: 100%;
            margin-top: 20px;
        }
        
        .branch-mini-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 16px;
            transition: all 0.3s ease;
        }
        
        .branch-mini-card:hover {
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(255, 255, 255, 0.1);
        }
        </style>
    """), unsafe_allow_html=True)

    settings = get_app_settings()
    region_sol = str(settings.region_code).zfill(4)

    # 1. Fetch DB records
    staff_list = master_service.repo.get_by_category("STAFF")
    units_list = master_service.repo.get_by_category("UNIT")
    depts_list = master_service.repo.get_by_category("DEPT")

    # Helper function to find a staff member by roll number
    def find_staff(roll: str | None) -> dict | None:
        if not roll: return None
        s = next((item for item in staff_list if str(item.code) == str(roll)), None)
        if s:
            meta = s.metadata or {}
            mobile = meta.get("mobile", "")
            if mobile:
                mobile = str(mobile).replace(".0", "").strip()
            return {
                "roll": s.code,
                "name": s.name_en,
                "grade": meta.get("grade", "N/A"),
                "mobile": mobile or "N/A",
                "designation": meta.get("designation", "Officer")
            }
        return None

    # Fetch Regional Office Unit
    ro_unit = next((u for u in units_list if str(u.code).zfill(4) == region_sol), None)
    
    ro_head = None
    ro_second = None
    if ro_unit:
        ro_meta = ro_unit.metadata or {}
        ro_head = find_staff(ro_meta.get("headUserId"))
        ro_second = find_staff(ro_meta.get("secondLineUserId"))

    # Fallback/dynamic lookups in case the head is mapped directly via staff status
    if not ro_head:
        for s in staff_list:
            meta = s.metadata or {}
            if str(meta.get("sol")).zfill(4) == region_sol and meta.get("status") == "BH":
                ro_head = find_staff(s.code)
                break
    if not ro_second:
        for s in staff_list:
            meta = s.metadata or {}
            if str(meta.get("sol")).zfill(4) == region_sol and meta.get("status") in ["2nd", "2nd Line"]:
                ro_second = find_staff(s.code)
                break

    # RENDER LEADERSHIP HIERARCHY
    st.markdown("### 👑 Regional Office Leadership")
    
    st.markdown('<div class="org-container">', unsafe_allow_html=True)
    
    # Render Regional Head (Level 1)
    if ro_head:
        st.markdown(clean_html(f"""
            <div class="org-card org-leader-card">
                <div class="org-badge org-leader-badge">⭐ Regional Head</div>
                <div class="org-name">{ro_head['name']}</div>
                <div class="org-title">{ro_head['designation']} ({ro_head['grade']})</div>
                <div class="org-contact">📞 {ro_head['mobile']}</div>
            </div>
        """), unsafe_allow_html=True)
    else:
        st.markdown(clean_html("""
            <div class="org-card org-leader-card">
                <div class="org-badge org-leader-badge">⭐ Regional Head</div>
                <div class="org-name">The Regional Manager</div>
                <div class="org-title">Regional Head (Scale V/VI)</div>
                <div class="org-contact">📞 N/A</div>
            </div>
        """), unsafe_allow_html=True)
        
    st.markdown('<div class="org-connector"></div>', unsafe_allow_html=True)
    
    # Render Regional 2nd Line (Level 2)
    if ro_second:
        st.markdown(clean_html(f"""
            <div class="org-card">
                <div class="org-badge">👥 Regional 2nd Line</div>
                <div class="org-name">{ro_second['name']}</div>
                <div class="org-title">{ro_second['designation']} ({ro_second['grade']})</div>
                <div class="org-contact">📞 {ro_second['mobile']}</div>
            </div>
        """), unsafe_allow_html=True)
    else:
        st.markdown(clean_html("""
            <div class="org-card">
                <div class="org-badge">👥 Regional 2nd Line</div>
                <div class="org-name">The Asst. General Manager</div>
                <div class="org-title">2nd Line Officer (Scale IV)</div>
                <div class="org-contact">📞 N/A</div>
            </div>
        """), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # RENDER REGIONAL DEPARTMENTS
    st.divider()
    st.markdown("### 🏢 Specialized Departments (Regional Office)")
    
    # Map department codes/names to active department officers
    ro_departments = {}
    for s in staff_list:
        meta = s.metadata or {}
        if str(meta.get("sol")).zfill(4) == region_sol:
            s_depts = meta.get("departments", [])
            if isinstance(s_depts, list):
                for d_code in s_depts:
                    if d_code not in ro_departments:
                        ro_departments[d_code] = []
                    
                    mobile = meta.get("mobile", "")
                    if mobile:
                        mobile = str(mobile).replace(".0", "").strip()
                    ro_departments[d_code].append({
                        "roll": s.code,
                        "name": s.name_en,
                        "grade": meta.get("grade", "Officer"),
                        "designation": meta.get("designation", "Officer"),
                        "mobile": mobile or "N/A"
                    })

    if not ro_departments:
        st.info("No specialized department officers are currently registered at the Regional Office.")
    else:
        GRADE_RANK = {
            "SRM": 7, "SM V": 6, "SM IV": 5, "MM III": 4, "MM II": 3, "JM I": 2, "CLERICAL": 1, "SWEEPER": 0
        }
        
        # Invert hierarchy: Group by Department Head -> Department -> Staff
        head_to_depts = {}
        for d_code in ro_departments:
            members = ro_departments[d_code]
            # Sort members by Grade rank (highest first) to identify the Department Head
            members.sort(key=lambda m: GRADE_RANK.get(str(m["grade"]).upper().strip(), 0), reverse=True)
            
            dept_head = members[0]
            dept_team = members[1:]
            
            head_roll = dept_head["roll"]
            if head_roll not in head_to_depts:
                head_to_depts[head_roll] = {
                    "info": {
                        "name": dept_head["name"],
                        "grade": dept_head["grade"],
                        "designation": dept_head["designation"],
                        "mobile": dept_head["mobile"]
                    },
                    "depts": {}
                }
            head_to_depts[head_roll]["depts"][d_code] = dept_team

        # Render one card per Department Head in a premium 3-column layout
        dept_cols = st.columns(3)
        for i, head_roll in enumerate(sorted(head_to_depts.keys(), key=lambda r: head_to_depts[r]["info"]["name"])):
            head_info = head_to_depts[head_roll]["info"]
            depts_led = head_to_depts[head_roll]["depts"]
            
            col_idx = i % 3
            with dept_cols[col_idx]:
                with st.container(border=True):
                    # Render Department Head Card Header (Gold Accent Box)
                    st.markdown(clean_html(f"""
                        <div style="background: rgba(251, 191, 36, 0.03); border-left: 4px solid #fbbf24; padding: 10px 14px; border-radius: 6px; margin: 4px 0 12px 0;">
                            <span style="font-size:0.65rem; text-transform:uppercase; color:#fbbf24; font-weight:800; letter-spacing:1.5px; display:block; margin-bottom:4px;">⭐ Department Head</span>
                            <div style="font-weight: 800; font-size: 1.05rem; color: #ffffff; line-height: 1.2;">{head_info['name']}</div>
                            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">{head_info['designation']} ({head_info['grade']})</div>
                            <div style="font-size: 0.75rem; color: #10b981; font-weight: 600; margin-top: 3px;">📞 {head_info['mobile']}</div>
                        </div>
                    """), unsafe_allow_html=True)
                    
                    # Render all departments led by this head and their team members (Staff)
                    for d_code in sorted(depts_led.keys()):
                        d_name = next((d.name_en for d in depts_list if str(d.code) == str(d_code)), str(d_code).upper())
                        team_members = depts_led[d_code]
                        
                        st.markdown(clean_html(f"""
                            <div style="margin-top: 8px; font-weight: 700; font-size: 0.85rem; color: #60a5fa;">
                                💼 Dept of {d_name}
                            </div>
                        """), unsafe_allow_html=True)
                        
                        if team_members:
                            for member in team_members:
                                st.markdown(clean_html(f"""
                                    <div style="background: rgba(255,255,255,0.02); border-left: 3px solid #3b82f6; padding: 5px 10px; border-radius: 4px; margin: 4px 0 4px 12px;">
                                        <div style="font-weight: 700; font-size: 0.8rem; color: #ffffff;">{member['name']} ({member['grade']})</div>
                                        <div style="font-size: 0.75rem; color: #94a3b8;">{member['designation']}</div>
                                        <div style="font-size: 0.75rem; color: #10b981; font-weight: 600; margin-top: 1px;">📞 {member['mobile']}</div>
                                    </div>
                                """), unsafe_allow_html=True)
                        else:
                            st.markdown(clean_html(f"""
                                <div style="font-size: 0.75rem; color: #64748b; font-style: italic; margin-left: 12px; margin-top: 2px;">
                                    • Sole Officer in Charge
                                </div>
                            """), unsafe_allow_html=True)

    # RENDER BRANCH NETWORK DIRECTORY
    st.divider()
    st.markdown("### 🏦 Branch Network Hierarchy")
    st.caption("Browse leadership details and contact channels for all units in our regional network.")

    # Search panel
    search_branch = st.text_input("🔍 Search Branch by SOL or Name", placeholder="e.g. Kosavapatti, 3347", key="org_chart_search")
    
    branch_units = [u for u in units_list if str(u.code).zfill(4) != region_sol and u.is_active]
    
    if search_branch:
        query = search_branch.lower().strip()
        branch_units = [
            u for u in branch_units 
            if query in str(u.code).lower() or query in u.name_en.lower() or query in str(u.metadata.get("district", "")).lower()
        ]

    if not branch_units:
        st.warning("No active branches matched your query.")
    else:
        cards_html = []
        for unit in sorted(branch_units, key=lambda x: x.name_en):
            u_meta = unit.metadata or {}
            b_head = find_staff(u_meta.get("headUserId"))
            b_second = find_staff(u_meta.get("secondLineUserId"))
            
            # Dynamic status fallback lookup
            if not b_head:
                b_head = next((find_staff(s.code) for s in staff_list if str(s.metadata.get("sol")).zfill(4) == str(unit.code).zfill(4) and s.metadata.get("status") == "BH"), None)
            if not b_second:
                b_second = next((find_staff(s.code) for s in staff_list if str(s.metadata.get("sol")).zfill(4) == str(unit.code).zfill(4) and s.metadata.get("status") in ["2nd", "2nd Line"]), None)

            # Build head details
            head_str = f"👤 <strong>{b_head['name']}</strong> ({b_head['grade']})<br><span style='color:#10b981; font-weight:600; font-size:0.8rem;'>📞 {b_head['mobile']}</span>" if b_head else "👤 <em>None Assigned</em>"
            # Build second line details
            second_str = f"👥 <strong>{b_second['name']}</strong> ({b_second['grade']})<br><span style='color:#10b981; font-weight:600; font-size:0.8rem;'>📞 {b_second['mobile']}</span>" if b_second else "👥 <em>None Assigned</em>"

            # Fetch other staff members posted to this branch SOL
            other_staff = []
            for s in staff_list:
                s_meta = s.metadata or {}
                if str(s_meta.get("sol", "")).zfill(4) == str(unit.code).zfill(4):
                    is_bh = b_head and str(s.code) == str(b_head["roll"])
                    is_2nd = b_second and str(s.code) == str(b_second["roll"])
                    if not is_bh and not is_2nd:
                        mobile = s_meta.get("mobile", "")
                        if mobile:
                            mobile = str(mobile).replace(".0", "").strip()
                        other_staff.append({
                            "name": s.name_en,
                            "grade": s_meta.get("grade", "N/A"),
                            "designation": s_meta.get("designation", "Officer"),
                            "mobile": mobile or "N/A"
                        })

            other_staff_html = ""
            if other_staff:
                staff_items = []
                for s in other_staff:
                    staff_items.append(f"""
                        <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.03); font-size: 0.8rem; color: rgba(255,255,255,0.65);">
                            👤 <strong>{s['name']}</strong> ({s['grade']})<br>
                            <span style="font-size: 0.75rem; color: #94a3b8;">{s['designation']}</span> | 
                            <span style="font-size: 0.75rem; color: #10b981; font-weight: 500;">📞 {s['mobile']}</span>
                        </div>
                    """)
                other_staff_html = f"""
                    <div style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px;">
                        <span style="font-size:0.7rem; text-transform:uppercase; color:#60a5fa; font-weight:700; letter-spacing:1px; display:block; margin-bottom:4px;">👥 Other Branch Staff</span>
                        {"".join(staff_items)}
                    </div>
                """

            cards_html.append(clean_html(f"""
                <div class="branch-mini-card">
                    <div style="font-weight: 800; font-size: 1.05rem; color: #60a5fa; margin-bottom: 2px;">{unit.name_en}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500; margin-bottom: 12px;">SOL {unit.code} | District: {u_meta.get('district', 'N/A')}</div>
                    
                    <div style="font-size: 0.85rem; color: rgba(255,255,255,0.7); line-height: 1.5;">
                        <div style="margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 6px;">
                            <span style="font-size:0.7rem; text-transform:uppercase; color:#fbbf24; font-weight:700; letter-spacing:1px; display:block;">Branch Head</span>
                            {head_str}
                        </div>
                        <div>
                            <span style="font-size:0.7rem; text-transform:uppercase; color:#a78bfa; font-weight:700; letter-spacing:1px; display:block;">2nd Line Officer</span>
                            {second_str}
                        </div>
                        {other_staff_html}
                    </div>
                </div>
            """))

        full_grid_html = f'<div class="org-branch-grid">{"".join(cards_html)}</div>'
        st.markdown(clean_html(full_grid_html), unsafe_allow_html=True)
