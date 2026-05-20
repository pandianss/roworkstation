from __future__ import annotations
import datetime
import pandas as pd

def clean_date(val: any) -> str:
    """Clean date parsing for Excel and DD.MM.YYYY formats."""
    if pd.isna(val) or str(val).lower() == "nat" or not str(val).strip():
        return ""
    
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime("%d.%m.%Y")
        
    # Handle DD.MM.YYYY
    s_val = str(val).strip()
    if "." in s_val and len(s_val.split(".")) == 3:
        try:
            d, m, y = s_val.split(".")
            # Ensure it's returned as DD.MM.YYYY or YYYY-MM-DD as per system standard
            # The original MasterService used YYYY-MM-DD for some parts but returned DD.MM.YYYY for others.
            # Let's stick to DD.MM.YYYY for display/storage consistency in Master records.
            return f"{d.zfill(2)}.{m.zfill(2)}.{y}"
        except Exception:
            pass
            
    # Remove time part if present (e.g. 2023-01-01 00:00:00)
    return s_val.split(" ")[0]
