from __future__ import annotations
import streamlit as st
from io import BytesIO
from PIL import Image
from src.interface.streamlit.components.primitives import render_action_bar
from src.interface.streamlit.state.services import get_doc_service_v4, get_master_service
from src.application.services.translation_service import DesignationMapper

def clean_str(val: any) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ["nan", "none"]:
        return ""
    return s

def clean_num(val: any) -> str:
    s = clean_str(val)
    if s.endswith(".0"):
        s = s[:-2]
    return s

def render() -> None:
    render_action_bar("Visiting Card Wizard", ["Design", "Preview", "Bulk Export"])
    
    doc_service = get_doc_service_v4()
    master_svc = get_master_service()
    
    st.markdown("### Create Your Institutional Visiting Card")
    st.caption("Generate professional, trilingual visiting cards with automatic front and back side rendering.")
    
    # Step 1: Data Intake
    with st.expander("Step 1: Staff Details", expanded=True):
        mode = st.radio("Intake Mode", ["Search Master", "Manual Entry"], horizontal=True)
        
        staff_data_list = []
        selected_staffs = []
        
        if mode == "Search Master":
            staff_list = master_svc.get_by_category("STAFF")
            selected_staffs = st.multiselect(
                "Select Staff Member(s)",
                staff_list,
                format_func=lambda s: f"{s.name_en} ({s.code}) - {s.metadata.get('designation', '') if s.metadata else ''}"
            )
            
            for s in selected_staffs:
                trans = DesignationMapper.get_trilingual(s.metadata.get("designation", "") if s.metadata else "")
                staff_data_list.append({
                    "name_en": s.name_en,
                    "name_hi": s.name_hi or s.name_en,
                    "name_ta": s.name_local or s.name_en,
                    "designation_en": s.metadata.get("designation", "") if s.metadata else "",
                    "designation_hi": trans.get("hi", ""),
                    "designation_ta": trans.get("ta", ""),
                    "mobile": clean_num(s.metadata.get("mobile", "")) if s.metadata else "",
                    "email": clean_str(s.metadata.get("email", "")) if s.metadata else "",
                    "phone": "0451-2420000", # Default for RO
                    "web": "www.iob.in"
                })
        else:
            data = {}
            col1, col2 = st.columns(2)
            data["name_en"] = col1.text_input("Name (English)", "RAJEEV KUMAR")
            data["name_hi"] = col2.text_input("Name (Hindi)", "राजीव कुमार")
            data["name_ta"] = st.text_input("Name (Tamil)", "ராஜீவ் குமார்")
            
            col3, col4, col5 = st.columns(3)
            data["designation_en"] = col3.text_input("Designation (En)", "Manager")
            data["designation_hi"] = col4.text_input("Designation (Hi)", "प्रबंधक")
            data["designation_ta"] = col5.text_input("Designation (Ta)", "மேலாளர்")
            
            col6, col7 = st.columns(2)
            data["mobile"] = col6.text_input("Mobile", "+91 99999 99999")
            data["email"] = col7.text_input("Email", "staff@iob.in")
            
            data["phone"] = st.text_input("Office Phone", "0451-2420000")
            data["web"] = st.text_input("Website", "www.iob.bank.in")
            
            staff_data_list.append(data)
            
        # Common address fields for all selected
        st.markdown("---")
        st.caption("Common Office Address")
        
        # Select unit to load address from
        unit_list = master_svc.get_by_category("UNIT")
        
        # Default to first selected staff's SOL, or Regional Office (3933)
        default_unit_idx = 0
        ro_unit_idx = 0
        for i, u in enumerate(unit_list):
            if u.code == "3933":
                ro_unit_idx = i
                break
        
        default_unit_idx = ro_unit_idx
        if selected_staffs:
            sol = selected_staffs[0].metadata.get("sol")
            for i, u in enumerate(unit_list):
                if u.code == sol:
                    default_unit_idx = i
                    break
                    
        selected_unit = st.selectbox(
            "Select Office/Branch to fetch address from",
            options=unit_list,
            index=default_unit_idx,
            format_func=lambda u: f"{u.code} - {u.name_en}"
        )
        
        # Default values fallback
        default_addr_en = "Regional Office, Dindigul\nNo. 17-i, First Floor, Pensioner Street\nPalani Road, Dindigul - 624001"
        default_addr_hi = "क्षेत्रीय कार्यालय, डिंडीगुल\n#17-i, पहली मंज़िल, पेंशनर स्ट्रीट\nपलनी रोड, दिण्डुक्कल - 624001"
        default_addr_ta = "மண்டல அலுவலகம், திண்டுக்கல்\n#17-i, முதல் தளம், பென்ஷனர் வீதி\nபழனி ரோடு, திண்டுக்கல் - 624001"

        if selected_unit:
            u_meta = selected_unit.metadata or {}
            
            # Fetch address 1, 2, 3 and pincode for each language and clean them
            addr1_en = clean_str(u_meta.get("address1_en", ""))
            addr2_en = clean_str(u_meta.get("address2_en", ""))
            addr3_en = clean_str(u_meta.get("address3_en", ""))
            
            addr1_hi = clean_str(u_meta.get("address1_hi", ""))
            addr2_hi = clean_str(u_meta.get("address2_hi", ""))
            addr3_hi = clean_str(u_meta.get("address3_hi", ""))
            
            addr1_ta = clean_str(u_meta.get("address1_ta", ""))
            addr2_ta = clean_str(u_meta.get("address2_ta", ""))
            addr3_ta = clean_str(u_meta.get("address3_ta", ""))
            
            pin = clean_str(u_meta.get("pincode", ""))
            try:
                if pin and "." in pin:
                    pin = str(int(float(pin)))
            except:
                pass
                
            # Construct English:
            # Row 1: address 1
            # Row 2: address 2
            # Row 3: address 3 & pincode
            if addr1_en or addr2_en:
                default_addr_en_parts = []
                if addr1_en: default_addr_en_parts.append(addr1_en)
                if addr2_en: default_addr_en_parts.append(addr2_en)
                
                row3_en = addr3_en
                if pin:
                    if row3_en:
                        row3_en = f"{row3_en} - {pin}"
                    else:
                        row3_en = f"{pin}"
                if row3_en: default_addr_en_parts.append(row3_en)
                default_addr_en = "\n".join(default_addr_en_parts)
            else:
                legacy_a1 = clean_str(u_meta.get("address1", ""))
                legacy_a2 = clean_str(u_meta.get("address2", ""))
                legacy_dist = clean_str(u_meta.get("district", ""))
                
                default_addr_en = clean_str(selected_unit.name_en)
                street_en = ", ".join([p for p in [legacy_a1, legacy_a2] if p])
                if street_en:
                    default_addr_en += f"\n{street_en}"
                
                row3_legacy = legacy_dist
                if pin:
                    if row3_legacy:
                        row3_legacy = f"{row3_legacy} - {pin}"
                    else:
                        row3_legacy = f"{pin}"
                if row3_legacy:
                    default_addr_en += f"\n{row3_legacy}"
            
            # Construct Hindi:
            if addr1_hi or addr2_hi:
                default_addr_hi_parts = []
                if addr1_hi: default_addr_hi_parts.append(addr1_hi)
                if addr2_hi: default_addr_hi_parts.append(addr2_hi)
                
                row3_hi = addr3_hi
                if pin:
                    if row3_hi:
                        row3_hi = f"{row3_hi} - {pin}"
                    else:
                        row3_hi = f"{pin}"
                if row3_hi: default_addr_hi_parts.append(row3_hi)
                default_addr_hi = "\n".join(default_addr_hi_parts)
            else:
                default_addr_hi = clean_str(selected_unit.name_hi)
                if pin:
                    default_addr_hi += f" - {pin}"
            
            # Construct Tamil:
            if addr1_ta or addr2_ta:
                default_addr_ta_parts = []
                if addr1_ta: default_addr_ta_parts.append(addr1_ta)
                if addr2_ta: default_addr_ta_parts.append(addr2_ta)
                
                row3_ta = addr3_ta
                if pin:
                    if row3_ta:
                        row3_ta = f"{row3_ta} - {pin}"
                    else:
                        row3_ta = f"{pin}"
                if row3_ta: default_addr_ta_parts.append(row3_ta)
                default_addr_ta = "\n".join(default_addr_ta_parts)
            else:
                default_addr_ta = clean_str(selected_unit.name_local)
                if pin:
                    default_addr_ta += f" - {pin}"

        # Post-clean trailing/leading cleanups defensively
        def final_clean(addr_str: str) -> str:
            lines = []
            for line in addr_str.split("\n"):
                cleaned_words = [w for w in line.split() if w.lower() != "nan"]
                cleaned = " ".join(cleaned_words)
                cleaned = cleaned.replace(" - - ", " - ").strip(" -").strip()
                if cleaned:
                    lines.append(cleaned)
            return "\n".join(lines)
            
        default_addr_en = final_clean(default_addr_en)
        default_addr_hi = final_clean(default_addr_hi)
        default_addr_ta = final_clean(default_addr_ta)

        # Determine dynamic Streamlit key suffix based on selected unit code
        sol_key = "default"
        if selected_unit:
            sol_key = str(selected_unit.code)
            
        addr_col1, addr_col2 = st.columns(2)
        common_addr_en = addr_col1.text_area("Address (English)", default_addr_en, key=f"addr_en_{sol_key}")
        common_addr_hi = addr_col2.text_area("Address (Hindi)", default_addr_hi, key=f"addr_hi_{sol_key}")
        common_addr_ta = st.text_area("Address (Tamil)", default_addr_ta, key=f"addr_ta_{sol_key}")

        # Resolve selected unit's contact details
        u_meta = selected_unit.metadata or {} if selected_unit else {}
        u_phone = clean_num(u_meta.get("phone", ""))
        if not u_phone:
            u_phone = "0451-2420000"
            
        u_email = clean_str(u_meta.get("email", ""))
        
        for d in staff_data_list:
            d["address_en"] = common_addr_en
            d["address_hi"] = common_addr_hi
            d["address_ta"] = common_addr_ta
            
            # Resolve email: pick from Staff Master if present; otherwise, fall back to Unit Master email
            staff_email = d.get("email", "").strip()
            if not staff_email or staff_email.lower() in ["nan", "none", "", "staff@iob.in"]:
                d["email"] = u_email
            else:
                d["email"] = staff_email
                
            d["phone"] = u_phone
            d["web"] = "www.iob.bank.in"

    # Step 2: Generation
    if st.button("Generate Cards", use_container_width=True, type="primary"):
        if not staff_data_list:
            st.warning("Please select at least one staff member.")
        else:
            all_pages = []
            with st.spinner(f"Rendering {len(staff_data_list)} Card(s)..."):
                for d in staff_data_list:
                    pages = doc_service.generate_visiting_card_image(d)
                    all_pages.extend(pages)
                st.session_state["vc_bulk_pages"] = all_pages
                st.session_state["vc_staff_count"] = len(staff_data_list)
            
    # Step 3: Display & Download
    if "vc_bulk_pages" in st.session_state:
        pages = st.session_state["vc_bulk_pages"]
        count = st.session_state["vc_staff_count"]
        
        st.markdown(f"### Preview ({count} Card(s) Generated)")
        
        # Show first card preview (Front & Back)
        if len(pages) >= 2:
            col_p1, col_p2 = st.columns(2)
            col_p1.image(pages[0], caption="Front Side (Trilingual)", use_container_width=True)
            col_p2.image(pages[1], caption="Back Side (Tamil)", use_container_width=True)
        
        st.markdown("---")
        col_dl1, col_dl2 = st.columns(2)
        
        # PNG Download (Zip or just first one)
        col_dl1.download_button(
            "Download First Card (PNG)",
            data=pages[0],
            file_name="VisitingCard_Front.png",
            mime="image/png",
            use_container_width=True
        )
        
        # PDF Generation (Multi-page)
        pdf_buf = BytesIO()
        pil_images = [Image.open(BytesIO(p)).convert("RGB") for p in pages]
        if pil_images:
            pil_images[0].save(
                pdf_buf, 
                format="PDF", 
                save_all=True, 
                append_images=pil_images[1:], 
                resolution=600.0
            )
            
            col_dl2.download_button(
                f"Download {count} Card(s) (PDF - {len(pages)} Pages)",
                data=pdf_buf.getvalue(),
                file_name="VisitingCards_Bulk.pdf",
                mime="application/pdf",
                use_container_width=True
            )
