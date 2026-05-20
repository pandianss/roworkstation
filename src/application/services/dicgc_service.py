from __future__ import annotations
from typing import List, Dict, Any
import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_
from src.infrastructure.persistence.database import engine
from src.infrastructure.persistence.sqlite_models import Base, DICGCReturnModel

# Ensure tables are created
Base.metadata.create_all(engine)

class DICGCService:
    def __init__(self, session: Session):
        self.session = session

    def save_return(self, data: Dict[str, Any]) -> DICGCReturnModel:
        # Work on a copy to avoid mutating the original dictionary (which might be in session state)
        data_copy = data.copy()
        
        # Convert date strings to date objects if necessary
        for key in ["half_year_ending", "debit_adjustment_date", "payment_date", "report_date"]:
            if key in data_copy and isinstance(data_copy[key], str):
                try:
                    data_copy[key] = datetime.datetime.strptime(data_copy[key], "%Y-%m-%d").date()
                except:
                    pass
        
        # Serialize breakup if it's a list/dict
        if "breakup" in data_copy:
            data_copy["breakup_json"] = json.dumps(data_copy.pop("breakup"))
        
        # Serialize sundry summary if it's a list/dict
        if "sundry_summary" in data_copy:
            data_copy["sundry_summary_json"] = json.dumps(data_copy.pop("sundry_summary"))

        new_return = DICGCReturnModel(**data_copy)
        self.session.add(new_return)
        self.session.commit()
        return new_return

    def get_returns(self) -> List[DICGCReturnModel]:
        return self.session.query(DICGCReturnModel).order_by(DICGCReturnModel.half_year_ending.desc()).all()

    def get_latest_return(self) -> DICGCReturnModel | None:
        return self.session.query(DICGCReturnModel).order_by(DICGCReturnModel.half_year_ending.desc()).first()

    def calculate_premium(self, assessable_deposits: float) -> Dict[str, float]:
        """
        Calculate premium and taxes.
        assessable_deposits is in Rs '000.
        Premium = 6 Paise per Rs 100 per half year.
        Premium = (Deposits * 1000) * (0.06 / 100) = Deposits * 0.6
        """
        premium = assessable_deposits * 0.6
        cgst = round(premium * 0.09, 2)
        sgst = round(premium * 0.09, 2)
        total_gst = cgst + sgst
        total_payable = round(premium + total_gst, 2)
        
        return {
            "premium": premium,
            "cgst": cgst,
            "sgst": sgst,
            "total_gst": total_gst,
            "total_payable": total_payable
        }
