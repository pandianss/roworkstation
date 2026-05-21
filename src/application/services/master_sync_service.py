from __future__ import annotations
import pandas as pd
import datetime
import os
import json
import logging
from src.core.paths import project_path
from src.core.utils.date_utils import clean_date
from src.application.services.translation_service import DesignationMapper
from src.infrastructure.persistence.master_repository import MasterRepository
from src.domain.models.master import MasterRecord

logger = logging.getLogger(__name__)

class MasterSyncService:
    def __init__(self, repo: MasterRepository | None = None) -> None:
        self.repo = repo or MasterRepository()

    def sync_staff_from_csv(self) -> None:
        """Ingest staff from CSV or Excel files, including seeding files."""
        project_root = project_path("files")
        excel_path = next(project_root.glob("Staff Details*.xlsx"), None)
        csv_path = project_path("files", "Staff.csv")
        base_df = pd.read_csv(csv_path) if csv_path.exists() else pd.DataFrame()
        
        if excel_path and excel_path.exists():
            logger.info(f"Sync: Found Excel source at {excel_path.name}")
            excel_df = pd.read_excel(excel_path)
            
            # Smart Merge: Use Excel as updates for existing CSV data
            if not base_df.empty:
                # Normalize columns for merging
                base_df.columns = [str(c).strip() for c in base_df.columns]
                excel_df.columns = [str(c).strip() for c in excel_df.columns]
                
                # Identify ID columns
                b_roll_col = next((c for c in base_df.columns if c.lower() in ["roll", "roll no", "rollno"]), "Roll No")
                e_roll_col = next((c for c in excel_df.columns if c.lower() in ["roll", "roll no", "rollno"]), None)
                
                if e_roll_col:
                    # Align Roll Nos
                    base_df[b_roll_col] = base_df[b_roll_col].astype(str).str.lstrip('0')
                    excel_df[e_roll_col] = excel_df[e_roll_col].astype(str).str.lstrip('0')
                    
                    # Merge: Excel overwrites common columns, preserves others
                    df = pd.merge(base_df, excel_df, left_on=b_roll_col, right_on=e_roll_col, how='outer', suffixes=('', '_new'))
                    
                    # Consolidate columns (Use _new values if available)
                    for col in base_df.columns:
                        if f"{col}_new" in df.columns:
                            df[col] = df[f"{col}_new"].fillna(df[col])
                            df.drop(columns=[f"{col}_new"], inplace=True)
                else:
                    df = excel_df # Fallback to excel if no roll col
            else:
                df = excel_df
        else:
            df = base_df
            
        if df.empty:
            logger.warning("No base staff data found. Skipping sync.")
            return
            
        seed_path = project_path("files", "StfData.csv")
        seed_df = pd.read_csv(seed_path) if seed_path.exists() else pd.DataFrame()
        
        df.columns = [str(c).strip() for c in df.columns]
        if not seed_df.empty:
            seed_df.columns = [str(c).strip() for c in seed_df.columns]
            s_roll_col = next((c for c in seed_df.columns if c.lower() in ["roll", "rollno", "roll no"]), None)
            if s_roll_col:
                seed_df[s_roll_col] = seed_df[s_roll_col].apply(lambda x: str(int(float(x))).lstrip('0') if pd.notna(x) else "")
                seed_df = seed_df.set_index(s_roll_col)
        
        staff_records = {}
        for r in self.repo.get_by_category("STAFF"):
            try:
                code_clean = str(int(float(str(r.code).strip()))).lstrip('0')
            except ValueError:
                code_clean = str(r.code).strip().lstrip('0')
            staff_records[code_clean] = r
        unit_records = {str(u.code).zfill(4): u for u in self.repo.get_by_category("UNIT")}
        
        to_save_staff = []
        to_save_units = {}
        incoming_rolls = set()
        
        for _, row in df.iterrows():
            try:
                r_map = {str(k).strip().lower(): v for k, v in row.items()}
                raw_roll = r_map.get("roll", r_map.get("roll no", r_map.get("rollno", "")))
                if not raw_roll: continue
                
                try:
                    roll_clean = str(int(float(str(raw_roll).strip()))).lstrip('0')
                    match_key = roll_clean
                except:
                    match_key = str(raw_roll).strip().lstrip('0')
                
                if not match_key: continue
                
                raw_sol = str(r_map.get("br cd", r_map.get("br code", r_map.get("branch sol", r_map.get("sol", ""))))).strip()
                if not raw_sol or raw_sol.lower() == "nan": continue
                
                try:
                    sol = str(int(float(raw_sol))).zfill(4)
                except:
                    sol = str(raw_sol).zfill(4)
                
                name_en = str(r_map.get("name", r_map.get("name (en)", ""))).strip()
                name_hi = str(r_map.get("name (hi)", "")).strip()
                name_ta = str(r_map.get("name (ta)", "")).strip()
                
                desig = str(r_map.get("designation", "")).strip()
                grade = str(r_map.get("grade", "")).strip()
                mobile = str(r_map.get("mobile number", r_map.get("mobile", ""))).strip()
                status = str(r_map.get("status", "")).strip()
                effective = str(r_map.get("effective", "")).strip()
                gender = str(r_map.get("gender", "M")).strip()
                
                dob = clean_date(r_map.get("date of birth", r_map.get("dob", "")))
                doj = clean_date(r_map.get("date of joining", r_map.get("doj", "")))
                dor = clean_date(r_map.get("date of retirement", r_map.get("dor", "")))
                
                if not seed_df.empty and match_key in seed_df.index:
                    s_row = seed_df.loc[match_key]
                    s_map = {str(k).strip().lower(): v for k, v in s_row.to_dict().items()}
                    s_dob = clean_date(s_map.get("dob", ""))
                    s_dor = clean_date(s_map.get("dor", ""))
                    if s_dob: dob = s_dob
                    if s_dor: dor = s_dor

                grade_wef = clean_date(r_map.get("current grade with effect from", r_map.get("grade wef", r_map.get("cugrwef", ""))))
                branch_wef = clean_date(r_map.get("current branch with effect from", r_map.get("branch wef", r_map.get("curbrwef", ""))))
                region_wef = clean_date(r_map.get("region with effect from", r_map.get("region wef", r_map.get("regwef", ""))))

                # Infer grade from designation if missing (Excel sources often lack it)
                if not grade or grade.strip() == "":
                    d_upper = desig.upper()
                    if "SR" in d_upper and "REGIONAL" in d_upper: grade = "SM V"
                    elif "CHIEF" in d_upper: grade = "SM IV"
                    elif "SENIOR MANAGER" in d_upper: grade = "MM III"
                    elif "MANAGER" in d_upper and "ASST" not in d_upper: grade = "MM II"
                    elif "ASST" in d_upper or "ASSISTANT" in d_upper: grade = "JM I"

                incoming_rolls.add(match_key)
                trilingual_desig = DesignationMapper.get_trilingual(desig)
                
                if match_key in staff_records:
                    staff = staff_records[match_key]
                    meta = dict(staff.metadata or {})
                    meta.update({
                        "sol": sol, 
                        "designation": desig,
                        "desig_en": trilingual_desig["en"],
                        "desig_hi": trilingual_desig["hi"],
                        "desig_ta": trilingual_desig["ta"],
                        "grade": grade or meta.get("grade", ""), # Keep old grade if new one is null
                        "mobile": mobile or meta.get("mobile", ""),
                        "status": status or meta.get("status", ""),
                        "gender": gender or meta.get("gender", "M"),
                        "dob": dob or meta.get("dob", ""),
                        "doj": doj or meta.get("doj", ""),
                        "dor": dor or meta.get("dor", ""),
                        "grade_wef": grade_wef or meta.get("grade_wef", ""),
                        "branch_wef": branch_wef or meta.get("branch_wef", ""),
                        "region_wef": region_wef or meta.get("region_wef", "")
                    })
                    staff.metadata = meta
                    # ONLY update names if non-empty (Preserve trilingual names if Excel lacks them)
                    if name_en: staff.name_en = name_en
                    if name_hi: staff.name_hi = name_hi
                    if name_ta: staff.name_local = name_ta
                    
                    staff.is_active = True
                    to_save_staff.append(staff)
                else:
                    new_staff = MasterRecord(
                        category="STAFF", code=match_key, 
                        name_en=name_en, name_hi=name_hi, name_local=name_ta,
                        is_active=True,
                        metadata={
                            "sol": sol, "designation": desig,
                            "desig_en": trilingual_desig["en"],
                            "desig_hi": trilingual_desig["hi"],
                            "desig_ta": trilingual_desig["ta"],
                            "grade": grade, "mobile": mobile, "status": status,
                            "gender": gender, "dob": dob, "doj": doj, "dor": dor,
                            "grade_wef": grade_wef, "branch_wef": branch_wef,
                            "region_wef": region_wef, "postings": []
                        }
                    )
                    to_save_staff.append(new_staff)
                
                if sol in unit_records:
                    unit = unit_records[sol]
                    u_meta = dict(unit.metadata or {})
                    assigned = False
                    if "BH" in status:
                        u_meta["headUserId"] = match_key
                        if effective and str(effective).lower() != "nan":
                            u_meta["authority_from"] = effective
                        assigned = True
                    elif "2nd" in status:
                        u_meta["secondLineUserId"] = match_key
                        assigned = True
                    
                    if assigned:
                        unit.metadata = u_meta
                        to_save_units[sol] = unit
            except Exception as e:
                logger.error(f"Error processing staff row: {e}", exc_info=True)
                continue
        
        if len(incoming_rolls) > (len(staff_records) * 0.5):
            for roll_match, staff in staff_records.items():
                if roll_match not in incoming_rolls:
                    staff.is_active = False
                    to_save_staff.append(staff)
        
        if to_save_staff:
            self.repo.save_all(to_save_staff)
        if to_save_units:
            self.repo.save_all(list(to_save_units.values()))

    def sync_units_from_csv(self) -> None:
        csv_path = project_path("files", "branches.csv")
        if not csv_path.exists(): return
        
        df = pd.read_csv(csv_path)
        df.columns = [c.strip() for c in df.columns]
        
        db_units = {str(u.code).zfill(4): u for u in self.repo.get_by_category("UNIT")}
        to_save = []
        incoming_codes = set()
        
        for _, row in df.iterrows():
            code = str(row["code"]).zfill(4)
            incoming_codes.add(code)
            raw_pin = str(row.get("pincode", row.get("Pincode", ""))).strip()
            if raw_pin.endswith(".0"):
                raw_pin = raw_pin[:-2]
            elif raw_pin.lower() in ["nan", "none"]:
                raw_pin = ""
                
            meta = {
                "type": str(row.get("type", "")),
                "district": str(row.get("district", row.get("District", ""))),
                "populationGroup": str(row.get("populationGroup", "")),
                "address1": str(row.get("Address1", row.get("address1", ""))),
                "address2": str(row.get("Address2", row.get("address2", ""))),
                "pincode": raw_pin,
                "address": str(row.get("address", "")),
                "address_hi": str(row.get("addressHi", "")),
                "address_ta": str(row.get("addressTa", "")),
                "address1_en": str(row.get("address1_en", "")),
                "address2_en": str(row.get("address2_en", "")),
                "address3_en": str(row.get("address3_en", "")),
                "address1_hi": str(row.get("address1_hi", "")),
                "address2_hi": str(row.get("address2_hi", "")),
                "address3_hi": str(row.get("address3_hi", "")),
                "address1_ta": str(row.get("address1_ta", "")),
                "address2_ta": str(row.get("address2_ta", "")),
                "address3_ta": str(row.get("address3_ta", "")),
                "size": str(row.get("size", "MEDIUM")),
                "openDate": str(row.get("openDate", ""))
            }
            if pd.notna(row.get("headUserId")): meta["headUserId"] = str(row["headUserId"])
            if pd.notna(row.get("secondLineUserId")): meta["secondLineUserId"] = str(row["secondLineUserId"])
            
            name_en = str(row.get("nameEn", ""))
            name_hi = str(row.get("nameHi", ""))
            name_ta = str(row.get("nameTa", ""))
            
            if code in db_units:
                unit = db_units[code]
                unit.name_en = name_en
                unit.name_hi = name_hi
                unit.name_local = name_ta
                old_meta = unit.metadata or {}
                old_meta.update(meta)
                unit.metadata = old_meta
                unit.is_active = True
                to_save.append(unit)
            else:
                new_unit = MasterRecord(
                    category="UNIT", code=code, name_en=name_en,
                    name_hi=name_hi, name_local=name_ta,
                    is_active=True, metadata=meta
                )
                to_save.append(new_unit)
                
        for code, unit in db_units.items():
            if code not in incoming_codes:
                unit.is_active = False
                to_save.append(unit)
                
        if to_save:
            self.repo.save_all(to_save)

    def sync_departments_from_csv(self) -> None:
        csv_path = project_path("files", "departments.csv")
        if not csv_path.exists(): return
        
        df = pd.read_csv(csv_path)
        df.columns = [c.strip() for c in df.columns]
        
        db_depts = {r.code: r for r in self.repo.get_by_category("DEPT")}
        to_save = []
        incoming_codes = set()
        
        for _, row in df.iterrows():
            code = str(row["dept_code"]).strip()
            incoming_codes.add(code)
            
            if code in db_depts:
                dept = db_depts[code]
                dept.name_en = str(row["dept_en"])
                dept.name_hi = str(row["dept_hi"])
                dept.name_local = str(row["dept_ta"])
                dept.metadata = {"email": str(row["email"])}
                dept.is_active = True
                to_save.append(dept)
            else:
                new_dept = MasterRecord(
                    category="DEPT", code=code, name_en=str(row["dept_en"]),
                    name_hi=str(row["dept_hi"]), name_local=str(row["dept_ta"]),
                    is_active=True, metadata={"email": str(row["email"])}
                )
                to_save.append(new_dept)
        
        for code, dept in db_depts.items():
            if code not in incoming_codes:
                dept.is_active = False
                to_save.append(dept)
                
        if to_save:
            self.repo.save_all(to_save)
