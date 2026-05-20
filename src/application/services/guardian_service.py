from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List

import pandas as pd

from src.core.paths import project_path
from src.domain.schemas.guardian import GuardianFollowUp
from src.domain.schemas.guardian_task import GuardianDailyTask
from src.infrastructure.persistence.json_repo import JsonRepository


class GuardianService:
    def __init__(self) -> None:
        self.repo = JsonRepository(project_path("data", "guardian_followups.json"), [])
        self.tasks_repo = JsonRepository(project_path("data", "guardian_tasks.json"), [])

    def record_followup(
        self,
        go_username: str,
        sol: str,
        details: str,
        category: str = "Other",
        status: str = "PENDING_BRANCH",
        priority: str = "P3",
    ) -> GuardianFollowUp:
        """Records a new structured branch follow-up observation."""
        records = self.repo.read()
        payload = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%d.%m.%Y"),
            "go_username": go_username,
            "sol": str(sol),
            "details": details,
            "category": category,
            "status": status,
            "priority": priority,
        }
        records.append(payload)
        self.repo.write(records)
        return GuardianFollowUp.model_validate(payload)

    def list_followups(self, sol: str | None = None, go_username: str | None = None) -> list[GuardianFollowUp]:
        """Lists logged follow-up observations, optionally filtered by branch SOL or officer username."""
        records = []
        for item in self.repo.read():
            try:
                records.append(GuardianFollowUp.model_validate(item))
            except Exception:
                # Handle backwards-compatibility gracefully
                normalized = dict(item)
                normalized.setdefault("category", "Other")
                normalized.setdefault("status", "PENDING_BRANCH")
                normalized.setdefault("priority", "P3")
                records.append(GuardianFollowUp.model_validate(normalized))

        if sol:
            records = [item for item in records if str(item.sol) == str(sol)]
        if go_username:
            records = [item for item in records if item.go_username == go_username]
        return records

    def create_daily_task(self, posted_by: str, title: str, description: str) -> GuardianDailyTask:
        """Creates a new shared daily operational focus/directive."""
        tasks = self.tasks_repo.read()
        payload = {
            "id": f"gt_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%d.%m.%Y"),
            "posted_by": posted_by,
            "title": title,
            "description": description,
        }
        tasks.append(payload)
        self.tasks_repo.write(tasks)
        return GuardianDailyTask.model_validate(payload)

    def list_daily_tasks(self, date_str: str | None = None) -> list[GuardianDailyTask]:
        """Lists daily shared tasks, optionally filtered by a specific date (dd.mm.yyyy)."""
        tasks = [GuardianDailyTask.model_validate(item) for item in self.tasks_repo.read()]
        if date_str:
            tasks = [t for t in tasks if t.date == date_str]
        return tasks

    def get_portfolio_mis(self, branch_sols: list[str]) -> list[dict]:
        """Aggregates high-performance MIS metrics filtered strictly for a portfolio of branch SOLs."""
        if not branch_sols:
            return []

        # Convert sols to list of integers for database querying
        sol_ints = []
        for s in branch_sols:
            try:
                sol_ints.append(int(s))
            except ValueError:
                continue

        from src.application.use_cases.mis.service import MISAnalyticsService
        from src.infrastructure.persistence.master_repository import MasterRepository

        mis_service = MISAnalyticsService()
        master_repo = MasterRepository()

        # Load latest master records for unit details
        units = {str(u.code): u.name_en for u in master_repo.get_by_category("UNIT")}

        # Fetch latest MIS data frame
        df = mis_service.get_data()
        if df.empty:
            return []

        latest_date = df["DATE"].max()
        latest_df = df[df["DATE"] == latest_date]

        # Filter strictly by portfolio SOLs
        portfolio_df = latest_df[latest_df["SOL"].isin(sol_ints)]
        
        results = []
        for _, row in portfolio_df.iterrows():
            sol_str = str(int(row["SOL"]))
            results.append({
                "sol": sol_str,
                "name": units.get(sol_str, f"Branch {sol_str}"),
                "advances": float(row.get("ADV", 0.0)),
                "deposits": float(row.get("TOTAL DEPOSITS", 0.0)),
                "cd_ratio": float(row.get("CD RATIO", 0.0)),
                "casa": float(row.get("CASA", 0.0)),
                "casa_ratio": round((float(row.get("CASA", 0.0)) / float(row.get("TOTAL DEPOSITS", 1.0)) * 100), 2) if float(row.get("TOTAL DEPOSITS", 0.0)) > 0 else 0.0,
                "npa": float(row.get("NPA", 0.0)),
                "npa_ratio": float(row.get("NPA %", 0.0)),
            })
        return results

    def compile_daily_report(self, date_str: str) -> dict:
        """Compiles all operational tasks and branch follow-ups for a specific day into a single dictionary."""
        # 1. Fetch directives posted today
        tasks = self.list_daily_tasks(date_str=date_str)
        
        # 2. Fetch all follow-ups logged today
        all_followups = []
        for item in self.repo.read():
            try:
                fup = GuardianFollowUp.model_validate(item)
            except Exception:
                normalized = dict(item)
                normalized.setdefault("category", "Other")
                normalized.setdefault("status", "PENDING_BRANCH")
                normalized.setdefault("priority", "P3")
                fup = GuardianFollowUp.model_validate(normalized)
            
            if fup.date == date_str:
                all_followups.append(fup)

        # 3. Resolve branch names & officer profiles
        from src.infrastructure.persistence.master_repository import MasterRepository
        master_repo = MasterRepository()
        units = {str(u.code): u.name_en for u in master_repo.get_by_category("UNIT")}
        staff = {s.code: s.name_en for s in master_repo.get_by_category("STAFF")}

        resolved_followups = []
        for f in all_followups:
            resolved_followups.append({
                "timestamp": f.timestamp.strftime("%H:%M:%S") if hasattr(f.timestamp, "strftime") else str(f.timestamp),
                "go_name": staff.get(f.go_username, f.go_username),
                "sol": f.sol,
                "branch_name": units.get(str(f.sol), f"Branch {f.sol}"),
                "details": f.details,
                "category": f.category,
                "status": f.status.replace("_", " "),
                "priority": f.priority,
            })

        return {
            "date": date_str,
            "directives": [t.model_dump() for t in tasks],
            "followups": resolved_followups,
        }

    def as_frame(self) -> pd.DataFrame:
        return pd.DataFrame(item.model_dump() for item in self.list_followups())
