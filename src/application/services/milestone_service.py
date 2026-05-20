from __future__ import annotations
from typing import Dict, List, Any
import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.infrastructure.persistence.database import engine
from src.infrastructure.persistence.sqlite_models import Base, MISRecordModel, MasterRecordModel

# Ensure tables are created
Base.metadata.create_all(engine)

class MilestoneService:
    """Service to calculate business milestones across branches."""
    
    PARAMETERS = [
        "SB", "CD", "CASA", "TD", "Business", 
        "Advances", "Jewel", "Housing", "Vehicle", 
        "Core Agri", "MSME", "Core Retail"
    ]

    def __init__(self, session: Session):
        self.session = session

    @st.cache_data(show_spinner=False)
    def get_milestone_achievements(_self, target_date=None) -> List[Dict[str, Any]]:
        """Identifies branches that crossed a NEW milestone during the month of target_date."""
        import datetime
        if target_date:
            # If target_date is provided (e.g. "2026-05-01"), we find the max date in THAT month
            if isinstance(target_date, str):
                 target_date = datetime.date.fromisoformat(target_date)
            
            # Find the actual last reporting date in the requested month
            next_month = (target_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
            latest_date = _self.session.query(func.max(MISRecordModel.date)).filter(
                MISRecordModel.date >= target_date.replace(day=1),
                MISRecordModel.date < next_month
            ).scalar()
        else:
            latest_date = _self.session.query(func.max(MISRecordModel.date)).scalar()
            
        if not latest_date:
            return []
            
        # Previous month end to establish baseline
        prev_month_end = latest_date.replace(day=1) - datetime.timedelta(days=1)
        prev_date = _self.session.query(func.max(MISRecordModel.date)).filter(MISRecordModel.date <= prev_month_end).scalar()
        
        # Load baseline levels
        branches = _self.session.query(MasterRecordModel).filter(MasterRecordModel.category == 'UNIT').all()
        branch_map = {b.code: b.name_en for b in branches}
        
        baseline_levels = {}
        if prev_date:
            prev_recs = _self.session.query(MISRecordModel).filter(MISRecordModel.date == prev_date).all()
            for r in prev_recs:
                vals = _self._calculate_parameters(r)
                baseline_levels[r.sol] = {p: _self._get_milestone_level(vals.get(p, 0.0)) for p in _self.PARAMETERS}
                # Also store actual values for previous_value reporting
                for p in _self.PARAMETERS:
                    baseline_levels[r.sol][p + "_VAL"] = vals.get(p, 0.0)

        # Find all reporting dates in the current month, sorted ascending
        curr_month_dates = _self.session.query(MISRecordModel.date)\
            .filter(MISRecordModel.date > prev_month_end)\
            .filter(MISRecordModel.date <= latest_date)\
            .distinct().order_by(MISRecordModel.date.asc()).all()
        
        achievements = []
        # Track already recognized breakthroughs to find the FIRST occurrence
        recognized = set() # (sol, parameter, milestone)

        for (d_date,) in curr_month_dates:
            recs = _self.session.query(MISRecordModel).filter(MISRecordModel.date == d_date).all()
            
            # 1. Regional Milestone Check (Aggregate of all branches)
            regional_totals = {}
            for r in recs:
                if r.sol == 3933: continue
                vals = _self._calculate_parameters(r)
                for p, v in vals.items():
                    regional_totals[p] = regional_totals.get(p, 0.0) + v
            
            for param, reg_val in regional_totals.items():
                # Regional milestones use larger increments (e.g. 500Cr or just any 50Cr jump)
                # But for now, we'll use the same 50Cr logic as branches for consistency
                reg_level = _self._get_milestone_level(reg_val)
                
                # We need a baseline for the region too
                # For simplicity, we'll calculate it on the fly or from baseline_levels
                prev_reg_val = sum(baseline_levels.get(sol_code, {}).get(param + "_VAL", 0.0) for sol_code in baseline_levels if sol_code != 3933)
                prev_reg_level = _self._get_milestone_level(prev_reg_val)
                
                if reg_level > prev_reg_level and reg_level >= 50:
                    key = ("REGION", param, reg_level)
                    if key not in recognized:
                        achievements.append({
                            "sol": 0, # Placeholder for Region
                            "branch_name": "DINDIGUL REGION",
                            "parameter": param,
                            "value": reg_val,
                            "previous_value": prev_reg_val,
                            "milestone": f"{reg_level}Cr+",
                            "date": d_date,
                            "prev_date": prev_date
                        })
                        recognized.add(key)

            # 2. Individual Branch Milestone Check
            for r in recs:
                if r.sol == 3933: continue
                curr_vals = _self._calculate_parameters(r)
                
                for param in _self.PARAMETERS:
                    curr_val = curr_vals.get(param, 0.0)
                    curr_level = _self._get_milestone_level(curr_val)
                    
                    prev_level = baseline_levels.get(r.sol, {}).get(param, 0)
                    
                    if curr_level > prev_level and curr_level >= 50:
                        key = (r.sol, param, curr_level)
                        if key not in recognized:
                            achievements.append({
                                "sol": r.sol,
                                "branch_name": branch_map.get(str(r.sol), f"SOL {r.sol}"),
                                "parameter": param,
                                "value": curr_val,
                                "previous_value": baseline_levels.get(r.sol, {}).get(param + "_VAL", 0.0), 
                                "milestone": f"{curr_level}Cr+",
                                "date": d_date,
                                "prev_date": prev_date
                            })
                            recognized.add(key)
        return achievements

    @st.cache_data(show_spinner=False)
    def get_all_at_milestones(_self) -> List[Dict[str, Any]]:
        """Returns all branches currently at any milestone level for all parameters."""
        latest_date = _self.session.query(func.max(MISRecordModel.date)).scalar()
        if not latest_date:
            return []
            
        recs = _self.session.query(MISRecordModel).filter(MISRecordModel.date == latest_date).all()
        branches = _self.session.query(MasterRecordModel).filter(MasterRecordModel.category == 'UNIT').all()
        branch_map = {b.code: b.name_en for b in branches}
        
        results = []
        for r in recs:
            if r.sol == 3933: continue
            vals = _self._calculate_parameters(r)
            for param, val in vals.items():
                level = _self._get_milestone_level(val)
                if level >= 50:
                    results.append({
                        "sol": r.sol,
                        "branch_name": branch_map.get(str(r.sol), f"SOL {r.sol}"),
                        "parameter": param,
                        "value": val,
                        "milestone": f"{level}Cr+"
                    })
        return results

    def _get_milestone_level(self, val: float) -> int:
        """Returns the highest milestone level reached (multiple of 50)."""
        if val < 50:
            return 0
        return int(val // 50) * 50

    def _calculate_parameters(self, r: MISRecordModel) -> Dict[str, float]:
        """Maps DB fields to business parameters in Crores."""
        sb = r.sb / 100
        cd = r.cd / 100
        td = r.td / 100
        agri = r.core_agri / 100
        msme = r.msme / 100
        jewel = r.gold / 100
        housing = r.housing / 100
        vehicle = r.vehicle / 100
        
        core_retail = (
            r.housing + r.vehicle + r.personal + 
            r.education + r.mortgage + r.liquirent + r.other_retail
        ) / 100
        
        total_dep = sb + cd + td
        # Use raw ADV column for total advances as per user source of truth
        total_adv = r.adv / 100
        
        return {
            "SB": sb,
            "CD": cd,
            "CASA": sb + cd,
            "TD": td,
            "Business": total_dep + total_adv,
            "Advances": total_adv,
            "Jewel": jewel,
            "Housing": housing,
            "Vehicle": vehicle,
            "Core Agri": agri,
            "MSME": msme,
            "Core Retail": core_retail
        }
    def save_achievements(self, achievements: List[Dict[str, Any]]) -> int:
        """Persists breakthroughs to the database, ensuring accurate branch names and avoiding duplicates."""
        from src.infrastructure.persistence.sqlite_models import MilestoneAchievementModel
        new_count = 0
        total_count = len(achievements)
        
        for a in achievements:
            # Check if already exists
            exists = self.session.query(MilestoneAchievementModel).filter(
                MilestoneAchievementModel.sol == a["sol"],
                MilestoneAchievementModel.parameter == a["parameter"],
                MilestoneAchievementModel.milestone == a["milestone"],
                MilestoneAchievementModel.date == a["date"]
            ).first()
            
            if exists:
                # Update branch name in case it was previously stored with a placeholder (e.g. "SOL 1789")
                if exists.branch_name != a["branch_name"]:
                    exists.branch_name = a["branch_name"]
            else:
                new_ach = MilestoneAchievementModel(
                    sol=a["sol"],
                    branch_name=a["branch_name"],
                    parameter=a["parameter"],
                    milestone=a["milestone"],
                    value=a["value"],
                    previous_value=a.get("previous_value", 0.0),
                    date=a["date"]
                )
                self.session.add(new_ach)
                new_count += 1
        
        self.session.commit()
        return new_count
