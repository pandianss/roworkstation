from __future__ import annotations

import datetime
from typing import Any

import pandas as pd
from src.core.paths import project_path
from src.infrastructure.persistence.json_repo import JsonRepository


DEFAULT_RETURNS = [
    {
        "id": "ret_001",
        "title": "Weekly Liquidity Position",
        "frequency": "Weekly",
        "due_date": "2026-05-08",
        "status": "Pending",
        "owner_dept": "PLAN",
        "created_at": "2026-05-01T10:00:00"
    },
    {
        "id": "ret_002",
        "title": "Monthly MSME Achievement",
        "frequency": "Monthly",
        "due_date": "2026-05-05",
        "status": "Completed",
        "owner_dept": "ADVANCES",
        "created_at": "2026-04-30T14:20:00"
    }
]


class ReturnsService:
    def __init__(self) -> None:
        self.repo = JsonRepository(project_path("data", "returns.json"), DEFAULT_RETURNS)

    def get_all(self) -> list[dict[str, Any]]:
        return self.repo.read()

    def get_as_frame(self) -> pd.DataFrame:
        data = self.get_all()
        if not data:
            return pd.DataFrame(columns=["title", "frequency", "due_date", "status", "owner_dept"])
        df = pd.DataFrame(data)
        # Reorder columns for display
        cols = ["title", "frequency", "due_date", "status", "owner_dept"]
        existing = [c for c in cols if c in df.columns]
        return df[existing]

    def create_return(self, title: str, frequency: str, due_date: datetime.date, owner_dept: str) -> dict[str, Any]:
        records = self.get_all()
        new_record = {
            "id": f"ret_{len(records) + 1:03d}",
            "title": title,
            "frequency": frequency,
            "due_date": due_date.isoformat(),
            "status": "Pending",
            "owner_dept": owner_dept,
            "created_at": datetime.datetime.now().isoformat()
        }
        records.append(new_record)
        self.repo.write(records)
        return new_record

    def update_status(self, return_id: str, status: str) -> bool:
        records = self.get_all()
        for r in records:
            if r["id"] == return_id:
                r["status"] = status
                self.repo.write(records)
                return True
        return False
