from __future__ import annotations
import datetime
import logging
import math
from typing import List, Dict, Any
from src.infrastructure.persistence.master_repository import MasterRepository

logger = logging.getLogger(__name__)

class AnniversaryService:
    def __init__(self, repo: MasterRepository | None = None) -> None:
        self.repo = repo or MasterRepository()

    def get_upcoming_anniversaries(self, days: int = 15) -> List[Dict[str, Any]]:
        """Finds units celebrating anniversaries in the next N days."""
        units = self.repo.get_by_category("UNIT")
        today = datetime.date.today()
        upcoming = []

        for unit in units:
            meta = unit.metadata or {}
            open_date_str = meta.get("openDate")
            if not open_date_str or open_date_str == "nan":
                continue

            try:
                # Format: YYYY-MM-DD
                open_date = datetime.datetime.strptime(open_date_str, "%Y-%m-%d").date()
                
                # Anniversary is today's year, branch's month/day
                anniv_this_year = open_date.replace(year=today.year)
                
                # If anniversary already passed this year, check next year
                if anniv_this_year < today:
                    anniv_this_year = anniv_this_year.replace(year=today.year + 1)

                diff = (anniv_this_year - today).days
                if 0 <= diff <= days:
                    years = anniv_this_year.year - open_date.year
                    upcoming.append({
                        "sol": unit.code,
                        "name": unit.name_en,
                        "open_date": open_date,
                        "anniversary_date": anniv_this_year,
                        "years": years,
                        "days_to_go": diff
                    })
            except (TypeError, ValueError) as e:
                logger.warning("Skipping invalid opening date for SOL %s: %s", unit.code, e)
                continue

        # Sort by days remaining
        upcoming.sort(key=lambda x: x["days_to_go"])
        return upcoming

    def calculate_years(self, open_date_str: str) -> int:
        """Calculates years of service as of today's anniversary cycle."""
        try:
            open_date = self._parse_date(open_date_str)
            if not open_date: return 0
            today = datetime.date.today()
            return today.year - open_date.year
        except (TypeError, ValueError):
            return 0

    def get_staff_celebrations(self, days: int = 3) -> List[Dict[str, Any]]:
        """Finds staff with upcoming birthdays or retirement in the next N days."""
        staff_list = self.repo.get_by_category("STAFF")
        today = datetime.date.today()
        celebrations = []

        for staff in staff_list:
            meta = staff.metadata or {}
            dob_str = meta.get("dob")
            dor_str = meta.get("dor")
            
            # 1. Check Birthday
            if dob_str and dob_str != "nan":
                dob = self._parse_date(dob_str)
                if dob:
                    bday_this_year = dob.replace(year=today.year)
                    if bday_this_year < today:
                        bday_this_year = bday_this_year.replace(year=today.year + 1)
                    
                    diff = (bday_this_year - today).days
                    if 0 <= diff <= days:
                        celebrations.append({
                            "type": "BIRTHDAY",
                            "name": staff.name_en,
                            "roll": staff.code,
                            "event_date": bday_this_year,
                            "original_date": dob,
                            "days_to_go": diff,
                            "sol": meta.get("sol"),
                            "designation": meta.get("designation")
                        })

            # 2. Check Retirement
            if dor_str and dor_str != "nan":
                dor = self._parse_date(dor_str)
                if dor:
                    diff = (dor - today).days
                    if 0 <= diff <= days:
                        celebrations.append({
                            "type": "RETIREMENT",
                            "name": staff.name_en,
                            "roll": staff.code,
                            "event_date": dor,
                            "original_date": dor,
                            "days_to_go": diff,
                            "sol": meta.get("sol"),
                            "designation": meta.get("designation")
                        })

        celebrations.sort(key=lambda x: x["days_to_go"])
        return celebrations

    def _parse_date(self, date_str: str) -> datetime.date | None:
        """Robust date parsing for various CSV formats."""
        if isinstance(date_str, datetime.datetime):
            return date_str.date()
        if isinstance(date_str, datetime.date):
            return date_str
        if date_str is None:
            return None
        if isinstance(date_str, float) and math.isnan(date_str):
            return None
        date_text = str(date_str).strip()
        if not date_text or date_text.lower() in {"nan", "nat", "n/a", "none"}:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return datetime.datetime.strptime(date_text, fmt).date()
            except ValueError:
                continue
        return None
