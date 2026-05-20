from __future__ import annotations
import pandas as pd
from src.infrastructure.persistence.master_repository import MasterRepository

class MasterDataService:
    def __init__(self, repo: MasterRepository | None = None) -> None:
        self.repo = repo or MasterRepository()

    def get_units_frame(self) -> pd.DataFrame:
        records = self.repo.get_by_category("UNIT")
        staff = {s.code: s.name_en for s in self.repo.get_by_category("STAFF")}
        
        cols = ["Code", "Name", "Type", "District", "Population Group", "Head", "2nd Line", "Effective From", "Open Date", "Active"]
        data = []
        for r in records:
            meta = r.metadata or {}
            h_id = meta.get("headUserId")
            s_id = meta.get("secondLineUserId")
            
            data.append({
                "Code": str(r.code),
                "Name": r.name_en,
                "Type": meta.get("type"),
                "District": meta.get("district"),
                "Population Group": meta.get("populationGroup"),
                "Head": staff.get(str(h_id), "None") if h_id else "None",
                "2nd Line": staff.get(str(s_id), "None") if s_id else "None",
                "Effective From": pd.to_datetime(meta.get("authority_from"), errors='coerce'),
                "Open Date": pd.to_datetime(meta.get("openDate"), errors='coerce'),
                "Active": r.is_active
            })
        return pd.DataFrame(data, columns=cols)

    def get_departments_frame(self) -> pd.DataFrame:
        records = self.repo.get_by_category("DEPT")
        cols = ["Code", "Name (En)", "Name (Hi)", "Name (Ta)", "Email", "Active"]
        data = []
        for r in records:
            meta = r.metadata or {}
            data.append({
                "Code": r.code,
                "Name (En)": r.name_en,
                "Name (Hi)": r.name_hi or "",
                "Name (Ta)": r.name_local or "",
                "Email": meta.get("email", ""),
                "Active": r.is_active
            })
        return pd.DataFrame(data, columns=cols)

    def get_staff_frame(self) -> pd.DataFrame:
        staff = self.repo.get_by_category("STAFF")
        cols = [
            "Roll No", "Name (En)", "Name (Hi)", "Name (Ta)", 
            "Branch SOL", "Designation", "Designation (Hi)", "Designation (Ta)",
            "Grade", "Mobile", "Gender", "Departments",
            "Posting From", "Posting To", "DOB", "DOJ", "DOR", "Grade WEF", "Branch WEF", "Active"
        ]
        data = []
        for s in staff:
            meta = s.metadata or {}
            data.append({
                "Roll No": s.code,
                "Name (En)": s.name_en,
                "Name (Hi)": s.name_hi or "",
                "Name (Ta)": s.name_local or "",
                "Branch SOL": meta.get("sol", ""),
                "Designation": meta.get("designation", ""),
                "Designation (Hi)": meta.get("desig_hi", ""),
                "Designation (Ta)": meta.get("desig_ta", ""),
                "Grade": meta.get("grade", ""),
                "Mobile": meta.get("mobile", ""),
                "Gender": meta.get("gender", "M"),
                "Departments": ", ".join(meta.get("departments", [])) if isinstance(meta.get("departments"), list) else "",
                "Posting From": pd.to_datetime(meta.get("posting_from"), errors='coerce'),
                "Posting To": pd.to_datetime(meta.get("posting_to"), errors='coerce'),
                "DOB": pd.to_datetime(meta.get("dob"), errors='coerce'),
                "DOJ": pd.to_datetime(meta.get("doj"), errors='coerce'),
                "DOR": pd.to_datetime(meta.get("dor"), errors='coerce'),
                "Grade WEF": pd.to_datetime(meta.get("grade_wef"), errors='coerce'),
                "Branch WEF": pd.to_datetime(meta.get("branch_wef"), errors='coerce'),
                "Active": s.is_active
            })
        return pd.DataFrame(data, columns=cols)
