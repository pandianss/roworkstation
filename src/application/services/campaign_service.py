from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any
from src.core.paths import project_path

class CampaignService:
    def __init__(self):
        self.path = project_path("data", "campaigns.json")
        self._ensure_file()

    def _ensure_file(self):
        if not self.path.exists():
            self.path.write_text(json.dumps({"campaigns": []}, indent=4), encoding="utf-8")

    def get_all(self) -> List[Dict[str, Any]]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data.get("campaigns", [])
        except Exception:
            return []

    def save_all(self, campaigns: List[Dict[str, Any]]):
        self.path.write_text(json.dumps({"campaigns": campaigns}, indent=4), encoding="utf-8")

    def add_campaign(self, name: str, start_date: str, end_date: str, target_metric: str, target_value: float, branch_targets: Dict[str, float] = None, status: str = "Active"):
        campaigns = self.get_all()
        campaigns.append({
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "target_metric": target_metric,
            "target_value": target_value,
            "branch_targets": branch_targets or {},
            "status": status
        })
        self.save_all(campaigns)

    def update_campaign(self, index: int, updated_data: Dict[str, Any]):
        campaigns = self.get_all()
        if 0 <= index < len(campaigns):
            campaigns[index].update(updated_data)
            self.save_all(campaigns)

    def delete_campaign(self, index: int):
        campaigns = self.get_all()
        if 0 <= index < len(campaigns):
            campaigns.pop(index)
            self.save_all(campaigns)
